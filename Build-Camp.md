# Dirtlets Build Camp

A visual checklist for building and testing one prototype:

```mermaid
flowchart TD
    A([Start]) --> B

    subgraph BUILD[1. Build the robot]
        B[Confirm parts and design] --> C[Build chassis and drivetrain]
        C --> D[Install battery, regulator, and motor driver]
    end

    subgraph CONNECT[2. Add electronics]
        D --> E[Install ESP32 control board]
        E --> F[Install camera and RPLIDAR]
        F --> G[Connect to central computer over Wi-Fi]
    end

    subgraph TEST[3. Test the system]
        G --> H[Test motors and sensor data]
        H --> I[Test video streaming and object detection]
        I --> J[Test obstacle avoidance]
        J --> K[Run a small mapping trial]
    end

    K --> L{Does it work?}
    L -->|No| M[Repair or adjust the design]
    M --> H
    L -->|Yes| N([Prototype ready])

    classDef start fill:#263238,stroke:#263238,stroke-width:2px,color:#ffffff;
    classDef build fill:#ffffff,stroke:#52636b,stroke-width:1.5px,color:#263238;
    classDef connect fill:#edf3f5,stroke:#176b78,stroke-width:1.5px,color:#173f46;
    classDef test fill:#f7f8f8,stroke:#52636b,stroke-width:1.5px,color:#263238;
    classDef decision fill:#fff4d6,stroke:#b7791f,stroke-width:2px,color:#5f4313;
    class B,C,D build;
    class E,F,G connect;
    class H,I,J,K,M test;
    class A,N start;
    class L decision;
    style BUILD fill:#fafafa,stroke:#aab5b9,stroke-width:1px;
    style CONNECT fill:#f4f8f9,stroke:#8eafb5,stroke-width:1px;
    style TEST fill:#fafafa,stroke:#aab5b9,stroke-width:1px;
```

## Build Order

1. Confirm the parts and wiring plan.
2. Build the chassis and drivetrain.
3. Add power regulation and motor control.
4. Install the ESP32, camera, and RPLIDAR.
5. Connect the robot to the central computer.
6. Test movement, streaming, sensing, and obstacle avoidance.
7. Run a small mapping test and improve the design.

## Robot Control Loop

This shows how video and commands travel during operation:

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 70, "rankSpacing": 90, "diagramPadding": 20}, "themeVariables": {"fontSize": "18px"}}}%%
flowchart LR
    A[ESP32-CAM<br/>Captures video and sensor data]
    B[Wi-Fi hotspot<br/>Streams data]
    C[Central computer<br/>Runs Object_Detection_Test.py]
    D{What should the robot do?}
    E[Keep moving]
    F[Turn]
    G[Stop]
    H[Motor ESP32<br/>Controls drive and steering]
    I[Robot moves and sees new surroundings]

    A --> B --> C --> D
    D -->|Clear path| E
    D -->|Object to one side| F
    D -->|Obstacle too close| G
    E --> H
    F --> H
    G --> H
    H --> I
    I --> A

    classDef camera fill:#edf3f5,stroke:#176b78,stroke-width:1.5px,color:#173f46;
    classDef computer fill:#263238,stroke:#263238,stroke-width:2px,color:#ffffff;
    classDef decision fill:#fff4d6,stroke:#b7791f,stroke-width:2px,color:#5f4313;
    classDef command fill:#ffffff,stroke:#52636b,stroke-width:1.5px,color:#263238;
    classDef feedback fill:#f7f8f8,stroke:#52636b,stroke-width:1.5px,color:#263238;

    class A,B camera;
    class C computer;
    class D decision;
    class E,F,G,H command;
    class I feedback;
```

The loop repeats continuously: the camera sends new information, the central computer makes a decision, and the motor ESP32 carries out the command.


