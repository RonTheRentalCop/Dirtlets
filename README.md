# Dirtlets
Dirtlets are little robots that are being designed to be a proof of concept SWARM to navigate, map, and score terrain for lunar and planetary bases for human expansion.

Dirtlets are little robots designed to autonomously navigate, map, and record environmental conditions to collectively create a map of an area or multiple areas. They also use a leader election system based on a Health Score (HS) calculated from battery life, mobility, current location, and other metrics to determine which leader will transmit the gathered data back to the central computer.

Intellectual Property Claim: © George Koniaris 2026

## Assignment and Rationale

The full assignment rationale is also available in [Assignment-and-Rationale.md](Assignment-and-Rationale.md).

Traditional planetary exploration missions often depend on one extremely expensive rover or spacecraft. That approach can produce valuable research, but a single vehicle may cover limited ground and becomes a single point of failure if it is damaged or loses communication.

The Dirtlets proposal is to develop a swarm of tracked lunar and planetary rovers that can navigate autonomously and work together to cover more terrain. Each rover would use lidar to measure its surroundings and contribute data to a shared map. The central computer would combine the sensor data, analyze environmental conditions, and identify areas that may be suitable for landing or future habitation.

The swarm would also use a Health Score (HS) system. The score could consider battery level, mobility, sensor status, position, and communication quality. The rover with the strongest score in a local group could act as that group’s leader and relay information to the central computer. Leadership would be reassigned when another rover becomes better suited to the role.

When the central computer identifies a promising area, it can send navigation instructions back to the swarm. The rovers would travel safely to that location, spread out, and investigate the surrounding terrain. This approach distributes sensing across multiple lower-cost vehicles instead of depending on one expensive machine.

For the first prototype, the ESP32 boards will manage camera streaming, motor control, and basic sensor communication. A central computer will perform the more demanding tasks, including image recognition, lidar processing, mapping, and navigation decisions. This keeps the individual rover hardware affordable while preserving the computing power needed for analysis.

