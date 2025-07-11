# IPPS
A simulation of Inexpensive Peer to Peer Subsystem protocol using threads and sockets. What could go wrong?

# FEATURES

- [x] Each peer moves concurrently in a random direction
- [ ] Each peer can scan peers that are within its "WIFI" vicinity
- [ ] Network Reformation Process 
- [ ] Network Join
- [ ] Network Leave
- [ ] ??


# BUGS
- [ ] (Server): OSError: [WinError 10048] Only one usage of each socket address (protocol/network address/port) is normally permitted.
    - Happens with a small population of peers and after cycle > 200
    - Possible cause is the exhaustion of ports by peers. Introducing delays might solve the problem

- [ ] (Simulation): Even without delays, the simulation is not very fast (> 30s to reach round 20 with 10 peers)
    - Possible cause: not recycling threads after an action??