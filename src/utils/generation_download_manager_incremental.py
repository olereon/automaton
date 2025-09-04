    async def _find_download_boundary_incremental(self, page) -> Optional[Dict[str, Any]]:
        """Efficient incremental boundary detection - scan as we scroll, not all at once"""
        try:
            logger.info("🔍 Step 13: Starting incremental boundary scan with scan-as-you-scroll approach")
            
            # Load existing log entries for comparison
            if not hasattr(self, 'existing_log_entries'):
                self.existing_log_entries = self._load_existing_log_entries()
            
            logger.info(f"📚 Loaded {len(self.existing_log_entries)} existing log entries for boundary detection")
            
            # Track scanned container IDs to prevent duplicate scanning
            scanned_container_ids = set()
            total_containers_scanned = 0
            duplicates_found = 0
            scroll_attempts = 0
            max_scroll_attempts = 200
            consecutive_no_new = 0
            max_consecutive_no_new = 5
            
            container_selector = self.config.completed_task_selector
            
            while scroll_attempts < max_scroll_attempts and consecutive_no_new < max_consecutive_no_new:
                # STEP 1: Get currently visible containers
                logger.info(f"🔍 Scan iteration {scroll_attempts + 1}: Getting visible containers")
                all_containers = await page.query_selector_all(container_selector)
                
                # Filter out already scanned containers
                new_containers = []
                for container in all_containers:
                    try:
                        # Get container ID or unique identifier
                        container_id = await container.get_attribute('id')
                        if not container_id:
                            # Try to get unique text content as ID
                            text_content = await container.text_content() or ""
                            container_id = hash(text_content[:100])  # Use first 100 chars as ID
                        
                        if container_id not in scanned_container_ids:
                            new_containers.append((container, container_id))
                            scanned_container_ids.add(container_id)
                    except Exception as e:
                        logger.debug(f"Error getting container ID: {e}")
                        continue
                
                if not new_containers:
                    consecutive_no_new += 1
                    logger.info(f"   No new containers found (consecutive: {consecutive_no_new}/{max_consecutive_no_new})")
                    
                    if consecutive_no_new >= max_consecutive_no_new:
                        logger.info("✅ Reached end of generation list - no new containers after multiple scrolls")
                        break
                else:
                    consecutive_no_new = 0
                    logger.info(f"📊 Found {len(new_containers)} new containers to scan (total scanned: {total_containers_scanned})")
                
                # STEP 2: Scan only the NEW containers for boundary
                for container, container_id in new_containers:
                    total_containers_scanned += 1
                    
                    try:
                        # Check if this container has content (not queued/failed)
                        text_content = await container.text_content() or ""
                        
                        if "Queuing" in text_content or "Something went wrong" in text_content or "Video is rendering" in text_content:
                            status = "Queued" if "Queuing" in text_content else ("Failed" if "Something went wrong" in text_content else "Rendering")
                            logger.debug(f"⏭️ Container {total_containers_scanned}: {status}, skipping")
                            continue
                        
                        # Extract metadata from container
                        container_metadata = await self._extract_container_metadata(container, text_content)
                        if not container_metadata:
                            continue
                        
                        container_time = container_metadata.get('creation_time', '')
                        container_prompt = container_metadata.get('prompt', '')[:100]
                        
                        if not container_time or not container_prompt:
                            logger.debug(f"⚠️ Container {total_containers_scanned}: Missing metadata, skipping")
                            continue
                        
                        # Step 14: Compare with log entries 
                        has_matching_log_entry = False
                        for log_time, log_entry in self.existing_log_entries.items():
                            log_prompt = log_entry.get('prompt', '')[:100]
                            if log_time == container_time and log_prompt == container_prompt:
                                has_matching_log_entry = True
                                duplicates_found += 1
                                break
                        
                        if not has_matching_log_entry:
                            # Found the boundary - this container has no corresponding log entry
                            logger.info(f"✅ BOUNDARY FOUND at container #{total_containers_scanned}")
                            logger.info(f"   📊 Containers scanned: {total_containers_scanned}")
                            logger.info(f"   🔍 Duplicates found before boundary: {duplicates_found}")
                            logger.info(f"   📅 Boundary time: {container_time}")
                            logger.info(f"   📝 Boundary prompt: {container_prompt[:50]}...")
                            logger.info(f"   🔄 Found after {scroll_attempts + 1} scroll iterations")
                            
                            # Click this container to resume downloads
                            click_success = await self._click_boundary_container(container, total_containers_scanned)
                            
                            if click_success:
                                logger.info("✅ Gallery opened at boundary, resuming downloads")
                                return {
                                    'found': True,
                                    'container_index': total_containers_scanned,
                                    'creation_time': container_time,
                                    'prompt': container_prompt,
                                    'containers_scanned': total_containers_scanned,
                                    'duplicates_found': duplicates_found,
                                    'scroll_iterations': scroll_attempts + 1
                                }
                            else:
                                logger.warning("❌ Could not click boundary container")
                                return None
                        else:
                            if total_containers_scanned <= 5 or total_containers_scanned % 50 == 0:
                                logger.debug(f"✓ Container {total_containers_scanned}: Duplicate found, continuing scan")
                    
                    except Exception as e:
                        logger.debug(f"Error checking container {total_containers_scanned}: {e}")
                        continue
                
                # STEP 3: If no boundary found in current batch, scroll to reveal more
                # CRITICAL FIX: Always scroll when no boundary found, regardless of new containers
                # The issue was that scrolling only happened when new containers were found
                # But we need to scroll to LOAD more containers when none are new
                if consecutive_no_new < max_consecutive_no_new:
                    logger.info(f"🔄 No boundary found in current batch, scrolling to reveal more containers...")
                    
                    # ULTRA-AGGRESSIVE scrolling with comprehensive infinite scroll strategies
                    try:
                        # Get current page state for smart scrolling
                        viewport_height = await page.evaluate("window.innerHeight")
                        current_scroll = await page.evaluate("window.pageYOffset")
                        document_height = await page.evaluate("document.body.scrollHeight")
                        
                        logger.debug(f"   📊 Scroll state: current={current_scroll}, viewport={viewport_height}, document={document_height}")
                        
                        # Strategy 1: Multiple scroll approaches to trigger lazy loading
                        scroll_strategies = [
                            # Gradual scrolling (some sites need this)
                            {"method": "gradual", "steps": 3, "amount": 500},
                            # Large jump (force loading)
                            {"method": "jump", "steps": 1, "amount": viewport_height * 2},
                            # Bottom approach (scroll to current bottom)
                            {"method": "bottom", "steps": 1, "amount": document_height}
                        ]
                        
                        for strategy in scroll_strategies:
                            logger.debug(f"   🔄 Trying scroll strategy: {strategy['method']}")
                            
                            if strategy["method"] == "gradual":
                                # Gradual scrolling - some sites need this
                                for step in range(strategy["steps"]):
                                    step_scroll = current_scroll + (strategy["amount"] * (step + 1))
                                    await page.evaluate(f"window.scrollTo(0, {step_scroll})")
                                    await page.wait_for_timeout(500)  # Small wait between steps
                                    logger.debug(f"     Step {step+1}: scrolled to {step_scroll}")
                            elif strategy["method"] == "jump":
                                # Large jump scrolling
                                new_position = current_scroll + strategy["amount"]
                                await page.evaluate(f"window.scrollTo(0, {new_position})")
                                logger.debug(f"     Jump scroll: {current_scroll} → {new_position}")
                            elif strategy["method"] == "bottom":
                                # Scroll to current document bottom
                                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                                logger.debug(f"     Bottom scroll: to {document_height}")
                            
                            # Wait for each strategy
                            await page.wait_for_timeout(1000)
                        
                        # Strategy 2: Comprehensive event triggering for infinite scroll
                        try:
                            await page.evaluate("""
                                // Comprehensive scroll event triggering
                                const events = ['scroll', 'wheel', 'resize', 'touchstart', 'touchmove', 'touchend'];
                                events.forEach(eventType => {
                                    window.dispatchEvent(new Event(eventType, { bubbles: true }));
                                    document.dispatchEvent(new Event(eventType, { bubbles: true }));
                                });
                                
                                // Trigger on scroll containers too
                                const scrollContainers = document.querySelectorAll('[id*="scroll"], [class*="scroll"], [class*="container"]');
                                scrollContainers.forEach(container => {
                                    events.forEach(eventType => {
                                        container.dispatchEvent(new Event(eventType, { bubbles: true }));
                                    });
                                });
                                
                                // Force reflow/repaint
                                document.body.offsetHeight;
                            """)
                            logger.debug("   ✅ Triggered comprehensive scroll events")
                        except Exception as e:
                            logger.debug(f"   Event triggering failed: {e}")
                        
                        # Strategy 3: Wait for network activity with extended patience
                        loading_wait_attempts = 0
                        max_loading_attempts = 3
                        
                        while loading_wait_attempts < max_loading_attempts:
                            loading_wait_attempts += 1
                            logger.debug(f"   ⏳ Loading wait attempt {loading_wait_attempts}/{max_loading_attempts}")
                            
                            try:
                                # Wait for network activity to indicate new content loading
                                await page.wait_for_load_state("networkidle", timeout=3000)
                                logger.debug("   ✅ Network idle detected - content may have loaded")
                                break
                            except:
                                logger.debug("   ⏳ Network idle timeout - trying longer wait")
                                await page.wait_for_timeout(2000)
                        
                        # Strategy 4: Force DOM refresh and check for changes
                        try:
                            await page.evaluate("""
                                // Force DOM refresh techniques
                                window.scrollBy(0, 1);  // Tiny scroll to trigger events
                                window.scrollBy(0, -1); // Scroll back
                                
                                // Try to trigger intersection observer callbacks
                                if (window.IntersectionObserver) {
                                    // Create dummy observer to trigger callbacks
                                    const observer = new IntersectionObserver(() => {});
                                    const elements = document.querySelectorAll('div');
                                    elements.forEach(el => observer.observe(el));
                                    setTimeout(() => observer.disconnect(), 100);
                                }
                            """)
                            logger.debug("   ✅ Applied DOM refresh techniques")
                        except Exception as e:
                            logger.debug(f"   DOM refresh failed: {e}")
                        
                        # Strategy 5: Extended wait with scroll position monitoring
                        initial_scroll = await page.evaluate("window.pageYOffset")
                        extended_wait_time = 3000  # 3 seconds
                        
                        logger.debug(f"   ⏳ Extended wait ({extended_wait_time}ms) for lazy loading...")
                        await page.wait_for_timeout(extended_wait_time)
                        
                        final_scroll = await page.evaluate("window.pageYOffset")
                        final_document_height = await page.evaluate("document.body.scrollHeight")
                        
                        logger.debug(f"   📊 Final state: scroll={final_scroll}, doc_height={final_document_height}")
                        logger.debug(f"   📊 Changes: scroll_moved={final_scroll != initial_scroll}, height_changed={final_document_height != document_height}")
                        
                        # Log comprehensive scroll summary
                        if final_document_height > document_height:
                            logger.info(f"   🎉 SUCCESS: Document height increased from {document_height} to {final_document_height}")
                        else:
                            logger.warning(f"   ⚠️ Document height unchanged: {document_height} (may be at end of content)")
                            
                    except Exception as e:
                        # Ultra-aggressive fallback scrolling
                        logger.debug(f"   ⚠️ Advanced scroll failed, using ultra-aggressive fallback: {e}")
                        
                        try:
                            # Try multiple fallback scroll methods
                            await page.evaluate("window.scrollBy(0, 1500)")  # Large scroll
                            await page.wait_for_timeout(1000)
                            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")  # Scroll to bottom
                            await page.wait_for_timeout(2000)
                            await page.evaluate("window.scrollBy(0, 500)")  # Small additional scroll
                            await page.wait_for_timeout(1500)
                            logger.debug("   ✅ Ultra-aggressive fallback completed")
                        except Exception as fallback_e:
                            logger.debug(f"   ❌ Even fallback scrolling failed: {fallback_e}")
                            await page.wait_for_timeout(3000)  # Just wait if all else fails
                
                scroll_attempts += 1
                
                # Progress update every 10 scrolls
                if scroll_attempts % 10 == 0:
                    logger.info(f"🔄 Progress: {scroll_attempts} scroll iterations, {total_containers_scanned} containers scanned, {duplicates_found} duplicates")
            
            logger.warning(f"❌ No boundary found after {scroll_attempts} scroll iterations")
            logger.warning(f"   📊 Total containers scanned: {total_containers_scanned}")
            logger.warning(f"   📊 Total duplicates found: {duplicates_found}")
            return None
            
        except Exception as e:
            logger.error(f"Error in incremental boundary detection: {e}")
            return None