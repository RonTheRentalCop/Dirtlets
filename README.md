# Dirtlets
Dirtlets are little robots that are being designed to be a proof of concept SWARM to navigate, map, and score terrain for lunar and planetary bases for human expansion.

Dirtlets are little robots designed to autonomously navigate, map, and record environmental conditions to collectively create a map of an area or multiple areas. They also use a leader election system based on a Health Score (HS) calculated from battery life, mobility, current location, and other metrics to determine which leader will transmit the gathered data back to the central computer.

Intellectual Property Claim: © George Koniaris 2026

## Assignment and Rationale

The full assignment rationale is also available in [Assignment-and-Rationale.md](Assignment-and-Rationale.md).

Traditional planetary exploration missions often depend on one extremely expensive rover or spacecraft. That approach can produce valuable research, but a single vehicle may cover limited ground and becomes a single point of failure if it is damaged or loses communication.

The Dirtlets proposal is to develop a swarm of tracked lunar and planetary rovers that can navigate autonomously and work together to cover more terrain. Each rover would use lidar to measure its surroundings and contribute data to a shared map. The central computer would combine the sensor data, analyze environmental conditions, and identify areas that may be suitable for landing or future habitation.

Prototype design revision: the first practical prototype may use a larger wheeled chassis instead of the original tracked design. The wheeled option should make telemetry integration, electronics placement, wiring separation, waterproofing, weatherproofing, and maintenance easier. The tracked design remains part of the long-term planetary rover concept, but the prototype must first use a chassis large enough to safely contain the electronics and wiring.

Future rover direction: the physical rover design will move toward a smaller version of a Mars-rover-style platform. The swarm will operate autonomously as a coordinated heterogeneous system, meaning the robots will share a mission while using different hardware and specialties. Small squads of about three robots can travel together and divide tasks. A squad could include a terrain-mapping rover using lidar, a soil-analysis rover with science sensors, and a communication rover dedicated to relaying data between the squad and the central computer. Other rover types could record RGB video while navigating autonomously, or carry a robotic arm that an operator controls through an RGB-camera view to collect rocks and soil or help free a stuck rover.

The swarm would also use a Health Score (HS) system. The score could consider battery level, mobility, sensor status, position, and communication quality. The rover with the strongest score in a local group could act as that group’s leader and relay information to the central computer. Leadership would be reassigned when another rover becomes better suited to the role.

When the central computer identifies a promising area, it can send navigation instructions back to the swarm. The rovers would travel safely to that location, spread out, and investigate the surrounding terrain. This approach distributes sensing across multiple lower-cost vehicles instead of depending on one expensive machine.

For the first prototype, the ESP32 boards will manage camera streaming, motor control, and basic sensor communication. A central computer will perform the more demanding tasks, including image recognition, lidar processing, mapping, and navigation decisions. This keeps the individual rover hardware affordable while preserving the computing power needed for analysis.

Why this new design block exists: I am adding this because the project has moved from only thinking about one basic tracked robot to thinking about a complete rover system that I can actually build. I still want to keep the tracked rover idea, but I may start with a bigger wheeled rover that has enough room for the electronics, safe wire separation, waterproofing, weatherproofing, and telemetry equipment. The smaller Mars-rover-style design is easier for me to use as a first working example while I keep improving the tracked version.

The robots will not all be identical. They will work as an autonomous heterogeneous swarm, meaning they will cooperate but use different hardware systems. A squad of about three robots could include a soil robot, a communication robot, and a mapping robot with lidar and an RGB camera. Other robots could have a robotic arm controlled through a camera view so an operator can collect rocks or dirt, clear objects, or help a stuck rover. I am adding these roles because one robot does not need to carry every expensive sensor and tool.

The printer has also affected the design decision. It was a free printer from Facebook Marketplace that I repaired. It printed some of the gears, tracks, and axles correctly at first, but later it started making jumbled parts. I worked on trying to fix it for about three to four weeks with very little improvement. Since I cannot reliably print the tread parts yet, the larger wheeled prototype gives me a better chance to build and test the electronics and autonomous systems while I keep working on the printer.

