# Automaton Sequence Diagrams

## 1. Automation Execution Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI/GUI
    participant B as Builder
    participant E as Engine
    participant C as Controller
    participant PM as Performance Monitor
    participant U1 as Utils
    participant P as Playwright
    participant BR as Browser
    participant FS as File System

    U->>CLI: Run automation config
    CLI->>B: Load config file
    B->>B: Validate config
    B->>E: Create AutomationConfig
    E->>C: Initialize controller
    C->>C: Setup control signals
    C->>E: Controller ready
    E->>PM: Start monitoring
    PM->>PM: Initialize metrics
    
    E->>C: Start automation
    C->>C: Set state to RUNNING
    C->>E: Automation started
    
    loop For each action in sequence
        E->>C: Check control signals
        C-->>E: Continue execution
        
        E->>PM: Start action timer
        E->>U1: Execute action
        U1->>P: Browser interaction
        P->>BR: Perform action
        BR-->>P: Action result
        P-->>U1: Processed result
        U1-->>E: Action result
        
        E->>PM: Stop action timer
        PM->>PM: Record metrics
        
        E->>C: Update progress
        C->>C: Update completed actions
        
        alt Checkpoint needed
            E->>C: Save checkpoint
            C->>C: Create checkpoint data
            C->>FS: Write checkpoint file
            FS-->>C: Checkpoint saved
            C-->>E: Checkpoint ID
        end
    end
    
    E->>C: Complete automation
    C->>C: Set state to STOPPED
    C->>E: Automation completed
    
    E->>PM: Generate performance report
    PM-->>E: Performance summary
    
    E->>CLI: Final results
    CLI->>U: Display results
```

## 2. Control Signal Handling Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as CLI/GUI
    participant C as Controller
    participant E as Engine
    participant A as Action Executor
    participant P as Playwright
    participant BR as Browser

    Note over U,E: Automation running
    
    U->>CLI: Pause command
    CLI->>C: Pause automation
    C->>C: Set pause event
    C->>CLI: Pause acknowledged
    CLI->>U: Display paused state
    
    E->>C: Check control signals
    C-->>E: Pause detected
    E->>E: Pause execution
    E->>C: Update state to PAUSED
    
    Note over U,E: Automation paused
    
    U->>CLI: Resume command
    CLI->>C: Resume automation
    C->>C: Clear pause event
    C->>CLI: Resume acknowledged
    CLI->>U: Display resumed state
    
    E->>C: Check control signals
    C-->>E: Resume detected
    E->>E: Resume execution
    E->>C: Update state to RUNNING
    
    Note over U,E: Automation running
    
    U->>CLI: Stop command
    CLI->>C: Stop automation
    C->>C: Set stop event
    C->>CLI: Stop acknowledged
    CLI->>U: Display stopping
    
    E->>C: Check control signals
    C-->>E: Stop detected
    E->>A: Stop current action
    A->>P: Abort if needed
    P->>BR: Stop interaction
    E->>C: Update state to STOPPING
    E->>E: Cleanup resources
    E->>C: Update state to STOPPED
    C->>CLI: Final status
    CLI->>U: Display stopped
```

## 3. Download Management Sequence

```mermaid
sequenceDiagram
    participant E as Engine
    participant DM as Download Manager
    participant P as Playwright
    participant BR as Browser
    participant FS as File System
    participant CV as Checksum Verifier
    participant DL as Download Logger

    E->>DM: Handle download request
    DM->>DM: Determine download path
    DM->>P: Setup download expectation
    E->>P: Click download trigger
    P->>BR: Initiate download
    BR-->>P: Download info
    P-->>DM: Download object
    
    DM->>DM: Extract filename
    DM->>FS: Create directory structure
    FS-->>DM: Directory ready
    
    DM->>P: Save download
    P->>FS: Write file
    FS-->>P: File saved
    P-->>DM: Save complete
    
    DM->>CV: Verify download
    CV->>FS: Read file
    FS-->>CV: File content
    CV->>CV: Calculate checksum
    CV-->>DM: Verification result
    
    DM->>DL: Log download
    DL->>FS: Write log entry
    FS-->>DL: Log written
    DL-->>DM: Log complete
    
    DM-->>E: Download info
    E->>E: Process download result
```

## 4. Checkpoint Management Sequence

```mermaid
sequenceDiagram
    participant E as Engine
    participant C as Controller
    participant CS as Checkpoint Serializer
    participant FS as File System
    participant CD as Checkpoint Deserializer

    Note over E,C: Save checkpoint sequence
    E->>C: Save checkpoint
    C->>C: Collect state data
    C->>CS: Serialize checkpoint
    CS->>CS: Convert to JSON
    CS->>FS: Write checkpoint file
    FS-->>CS: File written
    CS-->>C: Serialization complete
    C->>C: Store checkpoint reference
    C-->>E: Checkpoint ID
    
    Note over E,C: Load checkpoint sequence
    E->>C: Load checkpoint
    C->>CD: Load checkpoint data
    CD->>FS: Read checkpoint file
    FS-->>CD: File content
    CD->>CD: Parse JSON
    CD->>CD: Create checkpoint object
    CD-->>C: Checkpoint loaded
    C->>C: Restore state
    C->>E: Restored checkpoint
    E->>E: Resume from checkpoint
```

## 5. Error Handling Sequence

```mermaid
sequenceDiagram
    participant E as Engine
    participant A as Action Executor
    participant EH as Error Handler
    participant EC as Error Classifier
    participant ER as Error Recoverer
    participant C as Controller
    participant L as Logger
    participant U as User Interface

    E->>A: Execute action
    A->>A: Perform action
    A->>EH: Error detected
    EH->>EC: Classify error
    EC->>EC: Determine error type
    
    alt Retryable error
        EC->>ER: Handle recovery
        ER->>ER: Apply retry logic
        ER->>A: Retry action
        A->>A: Perform action
        alt Retry successful
            A-->>E: Action completed
        else Retry failed
            ER->>EC: Retry exhausted
            EC->>C: Report error
            C->>L: Log error
            L-->>C: Log written
            C->>U: Notify user
            C->>E: Error status
        end
    else Non-retryable error
        EC->>C: Report error
        C->>L: Log error
        L-->>C: Log written
        C->>U: Notify user
        C->>E: Error status
    else Critical error
        EC->>C: Emergency stop
        C->>C: Set emergency stop
        C->>E: Stop signal
        E->>E: Cleanup resources
        C->>U: Notify user
    end
```

## 6. Performance Monitoring Sequence

```mermaid
sequenceDiagram
    participant E as Engine
    participant PM as Performance Monitor
    participant MC as Metrics Collector
    participant RP as Resource Profiler
    participant RG as Report Generator
    participant FS as File System
    participant U as User Interface

    Note over E,PM: Initialization
    E->>PM: Start monitoring
    PM->>MC: Initialize metrics
    PM->>RP: Start profiling
    RP->>RP: Setup resource monitoring
    
    loop During automation execution
        E->>PM: Start action timer
        Note over PM: Action execution
        E->>PM: Stop action timer
        PM->>MC: Record action metrics
        MC->>MC: Update metrics database
    end
    
    Note over PM,RP: Resource monitoring
    RP->>RP: Collect CPU usage
    RP->>RP: Collect memory usage
    RP->>RP: Collect network activity
    RP->>MC: Store resource metrics
    
    Note over E,PM: Automation completed
    E->>PM: Stop monitoring
    PM->>RP: Stop profiling
    PM->>RG: Generate report
    RG->>MC: Collect metrics
    RG->>RP: Collect resource data
    RG->>RG: Analyze performance
    RG->>FS: Save report
    FS-->>RG: Report saved
    RG->>PM: Report summary
    PM->>E: Performance data
    E->>U: Display performance summary
```

## 7. Plugin Extension Sequence

```mermaid
sequenceDiagram
    participant E as Engine
    participant PI as Plugin Interface
    participant PM as Plugin Manager
    participant BP as Built-in Plugin
    participant EP as Extension Point
    participant CP as Custom Plugin

    Note over E,PI: Plugin initialization
    E->>PI: Initialize plugins
    PI->>PM: Load plugins
    PM->>BP: Initialize built-in
    BP-->>PM: Built-in ready
    PM->>EP: Register extensions
    EP-->>PM: Extensions ready
    PM-->>PI: Plugins loaded
    PI-->>E: Plugins ready
    
    Note over E,CP: Custom plugin usage
    E->>PI: Request custom action
    PI->>EP: Find extension point
    EP->>CP: Execute custom plugin
    CP->>CP: Perform custom logic
    CP-->>EP: Custom result
    EP-->>PI: Processed result
    PI-->>E: Custom action result
    
    Note over E,BP: Built-in plugin usage
    E->>PI: Request built-in action
    PI->>EP: Find extension point
    EP->>BP: Execute built-in plugin
    BP->>BP: Perform built-in logic
    BP-->>EP: Built-in result
    EP-->>PI: Processed result
    PI-->>E: Built-in action result
```

## 8. Metadata Extraction Sequence

```mermaid
sequenceDiagram
    participant E as Engine
    participant ME as Metadata Extractor
    participant TE as Text Extractor
    participant AE as Attribute Extractor
    participant SE as Structure Extractor
    participant VE as Validation Engine
    participant P as Playwright
    participant BR as Browser
    participant SC as Schema

    E->>ME: Extract metadata request
    ME->>TE: Extract text content
    TE->>P: Get element text
    P->>BR: Query element
    BR-->>P: Element data
    P-->>TE: Text content
    TE-->>ME: Text extracted
    
    ME->>AE: Extract attributes
    AE->>P: Get element attributes
    P->>BR: Query element attributes
    BR-->>P: Attribute data
    P-->>AE: Attribute values
    AE-->>ME: Attributes extracted
    
    ME->>SE: Extract structure
    SE->>P: Get element structure
    P->>BR: Query element structure
    BR-->>P: Structure data
    P-->>SE: Structure information
    SE-->>ME: Structure extracted
    
    ME->>VE: Validate extraction
    VE->>SC: Get validation schema
    SC-->>VE: Schema definition
    VE->>VE: Validate against schema
    VE-->>ME: Validation result
    
    ME->>ME: Compile metadata
    ME-->>E: Extracted metadata
    E->>E: Process metadata
```

## 9. DOM Cache Optimization Sequence

```mermaid
sequenceDiagram
    participant E as Engine
    participant DO as DOM Cache Optimizer
    participant QC as Query Cache
    participant SC as Selector Cache
    participant OC as Optimization Cache
    participant P as Playwright
    participant BR as Browser

    Note over E,DO: Cache initialization
    E->>DO: Initialize cache
    DO->>QC: Setup query cache
    DO->>SC: Setup selector cache
    DO->>OC: Setup optimization cache
    DO-->>E: Cache ready
    
    Note over E,DO: First query (not cached)
    E->>DO: Query selector
    DO->>QC: Check query cache
    QC-->>DO: Cache miss
    DO->>SC: Check selector cache
    SC-->>DO: Cache miss
    DO->>OC: Check optimization cache
    OC-->>DO: Cache miss
    DO->>P: Execute query
    P->>BR: Query DOM
    BR-->>P: Query result
    P-->>DO: Raw result
    DO->>DO: Optimize result
    DO->>QC: Cache query
    DO->>SC: Cache selector
    DO->>OC: Cache optimization
    DO-->>E: Optimized result
    
    Note over E,DO: Second query (cached)
    E->>DO: Query selector
    DO->>QC: Check query cache
    QC-->>DO: Cache hit
    DO->>DO: Retrieve cached result
    DO-->>E: Cached result
    
    Note over E,DO: Cache invalidation
    E->>DO: Invalidate cache
    DO->>QC: Clear query cache
    DO->>SC: Clear selector cache
    DO->>OC: Clear optimization cache
    DO-->>E: Cache invalidated
```

## 10. Adaptive Timeout Management Sequence

```mermaid
sequenceDiagram
    participant E as Engine
    participant AT as Adaptive Timeout Manager
    participant TC as Timeout Calculator
    participant HM as History Manager
    participant AM as Adjustment Manager
    participant P as Playwright
    participant BR as Browser

    Note over E,AT: Timeout initialization
    E->>AT: Initialize timeout management
    AT->>HM: Load timeout history
    AT->>TC: Set initial timeout values
    AT-->>E: Timeout manager ready
    
    Note over E,AT: Action execution with timeout
    E->>AT: Start action with timeout
    AT->>TC: Calculate timeout
    TC->>HM: Get historical data
    HM-->>TC: Timeout history
    TC->>TC: Compute optimal timeout
    TC-->>AT: Timeout value
    AT->>E: Timeout value
    E->>P: Execute action with timeout
    P->>BR: Perform action
    
    alt Action completes within timeout
        BR-->>P: Action result
        P-->>E: Action completed
        E->>AT: Action completed
        AT->>HM: Record successful timeout
        AT->>AM: Analyze performance
        AM->>AM: Adjust timeout strategy
    else Action times out
        P-->>E: Timeout exceeded
        E->>AT: Timeout occurred
        AT->>HM: Record timeout failure
        AT->>AM: Analyze failure
        AM->>AM: Adjust timeout strategy
        AT->>E: Timeout handling result
    end
    
    Note over E,AT: Periodic optimization
    E->>AT: Optimize timeout settings
    AT->>HM: Get timeout history
    HM-->>AT: Complete history
    AT->>AM: Analyze patterns
    AM->>AM: Calculate optimal settings
    AM->>TC: Update timeout calculations
    TC-->>AT: Calculations updated
    AT-->>E: Optimization complete