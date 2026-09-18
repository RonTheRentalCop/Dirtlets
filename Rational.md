# Assignment #4

## Project Question

How can a group of affordable, autonomous rovers work together to map unfamiliar terrain and identify promising landing areas more efficiently than one large rover?

## Paragraph 1: Existing Knowledge and Engineering Background

Researchers and engineers have already shown that robotic spacecraft can collect scientific data in environments that are difficult or dangerous for people to reach. NASA's Mars rovers use cameras, spectrometers, drills, and other instruments to study rocks, soil, and the history of Mars (NASA, n.d.). Engineers have also created multi robot missions. NASA's Cooperative Autonomous Distributed Robotic Exploration, or CADRE, mission is designed to demonstrate several small rovers working together on the Moon (NASA, 2024).

Researchers and engineers learned these lessons by testing robots in laboratories, deserts, volcanic areas, and other difficult environments; developing sensors; and analyzing data from robotic missions. Multi robot research has also studied how robots can divide tasks and coordinate their actions (Gerkey & Mataric, 2004). Engineers still need to improve how low cost robots share information, maintain communication, select leaders, and continue working when one robot fails. The Dirtlets project addresses this challenge by proposing different rover roles, including scout rovers, science rovers, and communication or relay rovers. These roles could use similar tracked bases while carrying different sensors or equipment.

## Paragraph 2: Important Keywords and Concepts

### Swarm robotics

Swarm robotics is an approach in which multiple robots coordinate as one system. Each robot follows local rules and shares information, allowing the group to complete tasks that would be difficult for one robot. This idea is related to collective behavior in social insects, bird flocks, and schools of fish (Beni & Wang, 1993).

### Multi agent autonomous navigation

A multi agent system contains several independent agents, such as robots, that communicate and make decisions while sharing an environment. Autonomous navigation means that a robot uses sensors, a map, and programmed rules to move without continuous human control. The robots must avoid obstacles, maintain safe routes, and coordinate their actions.

### Lidar and RGB camera data

Lidar, or light detection and ranging, measures distance by sending out laser pulses and measuring how long their reflections take to return. It can create a point cloud, which is a group of measured points representing the shape of the surroundings (NASA Earthdata, n.d.). An RGB camera records ordinary red, green, and blue color images. Combining lidar with RGB video can provide both the shape and visual appearance of an environment, but the sensors must be time synchronized and spatially calibrated so their measurements line up correctly.

### Health Score (HS)

The Health Score is a proposed numerical value for estimating how capable each rover is at a given moment. It could include battery level, motor condition, sensor status, communication quality, position, and mobility. The score would help the swarm select a temporary local leader instead of depending on one permanent leader.

## Paragraph 3: Impact and Beneficiaries

The project could benefit planetary scientists, mission planners, astronauts, space agencies, and private aerospace companies. These groups need reliable information about terrain, hazards, resources, and possible landing locations before sending people or expensive equipment to another world. A concrete example is a group of Dirtlets surveying several possible landing zones while a central computer compares slope, obstacles, surface roughness, and other measurements. That information could help mission planners reject an unsafe site before a much more expensive landing attempt.

The project also has possible Earth based applications. Similar tracked robots could be adapted for tunnels, sewers, mines, industrial facilities, disaster areas, or other locations that are unsafe for people. Emergency response teams, infrastructure inspectors, and environmental researchers could benefit from robots that collect information while keeping people away from dangerous conditions.

My personal connection to this project is that I am interested in space exploration, robotics, and building a practical swarm system with limited resources. I want to investigate whether a group of simpler robots can collect useful information without requiring a very expensive computer on every rover. The project connects to larger challenges in space exploration: reducing mission cost, improving resilience, increasing the area that can be surveyed, and making exploration safer for future crews.

## Paragraph 4: Knowledge and Invention Gap

Existing missions demonstrate both advanced single rover exploration and the promise of coordinated small rovers, but there is still a practical gap between those systems and an affordable prototype. A low cost swarm must coordinate mapping, video, obstacle avoidance, communication, and leadership while using inexpensive hardware with limited processing power. It must also continue operating when a rover or communication link fails.

The specific gap addressed by this project is how to combine low cost ESP32 based rover hardware with central computer processing, lidar mapping, image recognition, and Health Score leadership in one workable system. This project will investigate whether the central computer can process streamed sensor data, maintain a shared map, select a capable local leader, and send safe navigation commands back to the swarm.

## Paragraph 5: Proposed Approach

To address this gap, I will build a proof of concept tracked rover using an ESP32 motor control board, an ESP32 camera, an RPLIDAR C1, an MPU 650, a motor driver, a UBEC regulator, a 3S LiPo battery, and two JGY 370 motors. The ESP32 boards will handle motor control, camera streaming, and basic sensor communication. A central computer will perform the more demanding operations.

The original tracked design remains the long-term goal, but the first physical prototype may need to pivot to a larger wheeled chassis. The tracked approach has been difficult to adapt because I do not currently have the right tread materials, and the first chassis was too small to fit larger treads that would provide easier land traversal. The larger wheeled platform should also provide more room for the electronics, safer separation between power and signal wiring, and space for waterproofing and weatherproofing. This change is a practical prototype decision and does not remove the tracked rover concept from the overall project.

The longer-term physical design will be a smaller version of a Mars-rover-style vehicle. The swarm will use a heterogeneous organization rather than giving every rover identical hardware. Each autonomous squad can contain roughly three specialized robots that cooperate while traveling together. One rover could focus on soil analysis, another could be dedicated to communication and telemetry relay, and another could use lidar and an RGB camera to navigate autonomously and record mapping data. A fourth type of rover could carry an arm controlled from an operator's RGB-camera view to collect rocks or soil, clear an obstruction, or help another rover escape when it becomes stuck. This organization allows the swarm to distribute expensive or specialized equipment instead of placing every sensor and tool on every robot.

The central computer will use OpenCV to receive and process video and an established image recognition library, such as YOLO through Ultralytics, to identify objects. It will combine the video, lidar, inertial, and movement data to build a map and make navigation decisions. The project will not build an object recognition model from scratch. Instead, it will study how an existing model can be integrated into a low cost multi rover system.

The robots will report their condition to the central computer. The computer will calculate a Health Score for each rover and use those scores to select a temporary local leader. The leader will help relay information from nearby rovers. If the leader's battery, mobility, sensors, or communication quality become worse, leadership can move to another rover. The central computer will then send commands for the group to travel safely, spread out, investigate an area, and update the shared map.

## Why I Added This Design Change

I am adding this section because the robot design has changed as I started thinking about what I can actually build and fit together. I still want the tracked rover idea for the bigger planetary version, but for the smaller prototype I want to move toward something that looks more like a smaller Mars rover. The original chassis and tread plan was giving me problems because I did not have the right materials for the treads and the chassis was too small to fit larger treads for easier land travel. I also need more room to separate the electronics and wires, protect the system from water and weather, and keep the telemetry system from becoming impossible to manage.

The swarm will not be made out of four exact copies of the same robot. I am planning a group of different robots that work together by using different hardware for different jobs. They can move in squads of about three, with one robot focused on soil analysis, one robot acting as a communication and telemetry relay, and one robot using lidar and an RGB camera to map and record the area. Another type of robot could have an arm that an operator controls through an RGB-camera view. That robot could collect rocks or dirt, clear an obstruction, or help another rover if it gets stuck.

This change does not erase the older tracked design or the writing about it. It adds a more realistic build direction for the first prototype. The main change is that the first rover may be larger and wheeled so I can fit the electronics and get the autonomous communication, mapping, and safety systems working before trying to build the more difficult tracked versions.

Another reason this change became necessary was my 3D printer. The printer was a free one I found on Facebook Marketplace that I repaired, so it already had problems before I started printing the rover parts. At first it seemed like the gears, tracks, and axles were printing fine, but then the parts started coming out jumbled and unusable. I tried to fix it for about three to four weeks and only made a small amount of improvement. This made the tread design even harder because I could not depend on the printer to repeatedly produce accurate track parts. Because of this, starting with a larger wheeled chassis is a more realistic way to get the first prototype moving while I continue working on the printer and the tracked design.

## Cohesive Rationale

Traditional planetary exploration often depends on one extremely expensive rover or spacecraft. These vehicles can produce valuable scientific results, but a single vehicle may cover limited ground and becomes a single point of failure if it is damaged or loses communication. Research from robotic missions has shown the value of remote sensing, while newer work such as NASA's CADRE mission demonstrates the potential of multiple small rovers coordinating on the Moon (NASA, n.d.; NASA, 2024). However, an affordable system that combines swarm coordination, lidar mapping, video recognition, central processing, and dynamic leadership still needs practical testing.

The Dirtlets project proposes a swarm of tracked rovers that can navigate autonomously and work together to survey unfamiliar terrain. For the first physical prototype, a larger wheeled platform may be used while the tracked design is developed further. Each rover would use lidar to measure distance, an RGB camera to provide visual information, and an inertial sensor to help estimate movement. A central computer would combine those streams into a shared map and analyze conditions such as obstacles, surface shape, and possible landing areas. A Health Score would compare each rover's battery, mobility, sensor condition, position, and communication quality so the swarm could select the most capable local leader and reassign leadership when necessary.

This approach could help planetary scientists, mission planners, astronauts, and aerospace companies evaluate terrain before sending people or expensive equipment. It could also be adapted for dangerous Earth environments such as mines, tunnels, sewers, industrial facilities, and disaster areas. My personal motivation is to explore whether a group of affordable robots can perform useful cooperative work instead of depending on one very expensive machine. For the first prototype, ESP32 boards will stream video and control the motors while a central computer performs image recognition, lidar processing, mapping, and navigation. By testing this architecture, the project will address a specific engineering gap: whether low cost rover hardware and shared central computation can support reliable multi robot exploration.

## Sources

Beni, G., & Wang, J. (1993). Swarm intelligence in cellular robotic systems. In Proceedings of NATO Advanced Workshop on Robots and Biological Systems, pages 703 to 712. Springer.

Gerkey, B. P., & Mataric, M. J. (2004). A formal analysis and taxonomy of task allocation in multi robot systems. The International Journal of Robotics Research, 23(9), 939 to 954.

NASA. (2024). NASA's CADRE rovers to explore the Moon in 2026. NASA.

NASA. (n.d.). Mars 2020 Perseverance rover. NASA Jet Propulsion Laboratory.

NASA Earthdata. (n.d.). Lidar. NASA Earthdata.

Adams, C., Smith, T., Woodard, A., Van Kints, E., Kempa, B., & Frank, J. (2024). Next-generation multi-agent swarm (NGS) study. NASA Ames Research Center.

Decentralized path planning in lunar robot swarms: Local optimization for collision avoidance under constrained perception. (2026). IEEE. [https://xplorestaging.ieee.org/document/11101941](https://xplorestaging.ieee.org/document/11101941)

E, J., Bao, R., Fan, J., Dai, Z., Cui, E., Li, N., & Wang, K. (2026). A scenario-driven review of multi-agent cooperation for lunar surface missions. Acta Astronautica, 248, 111-138. [https://www.sciencedirect.com/science/article/abs/pii/S0094576526003838?via%3Dihub](https://www.sciencedirect.com/science/article/abs/pii/S0094576526003838?via%3Dihub)

Hinchey, M. G., Sterritt, R., Rouff, C., Rash, J. L., & Truszkowski, W. F. (2005). Autonomous and autonomic swarms. In Proceedings of the 2005 International Conference on Software Engineering Research and Practice (SERP'05). CSREA Press.

Lunarminer framework for nature-inspired swarm robotics in lunar water ice extraction. (2024). Biomimetics, 9(11), 680. The original link is currently unavailable because the page was removed for maintenance.

Martinez Rocamora, B., Kilic, C., Tatsch, C., Pereira, G. A. S., & Gross, J. N. (2023). Multi-robot cooperation for lunar in-situ resource utilization. Frontiers in Robotics and AI, 10, 1149080. https://doi.org/10.3389/frobt.2023.1149080

NASA. (2025). What is NASA's Distributed Spacecraft Autonomy? NASA Ames Research Center. [https://www.nasa.gov/centers-and-facilities/ames/what-is-nasas-distributed-spacecraft-autonomy/](https://www.nasa.gov/centers-and-facilities/ames/what-is-nasas-distributed-spacecraft-autonomy/)

NASA Jet Propulsion Laboratory. (n.d.). CADRE (Cooperative Autonomous Distributed Robotic Exploration). [https://www.jpl.nasa.gov/missions/cadre/](https://www.jpl.nasa.gov/missions/cadre/)

REALMS2: Resilient exploration and lunar mapping system 2. (2025). arXiv.

SKiD-SLAM: Resource-aware distributed multi-robot LiDAR SLAM for planetary missions with field deployments at analog sites. (2026). IEEE Transactions on Field Robotics. GitHub: [https://github.com/sparolab/SKiD-SLAM](https://github.com/sparolab/SKiD-SLAM)

## YouTube Videos

DIY Autonomous ESP32 Robot (GPS, Obstacle Avoidance). [https://www.youtube.com/watch?v=neAgJPl7brA](https://www.youtube.com/watch?v=neAgJPl7brA)
