# Dataset Architecture & NSL-KDD Feature Breakdown

This document provides a detailed technical breakdown of the NSL-KDD dataset used for training and evaluating the Network Intrusion Detection System.

---

## 1. About NSL-KDD

NSL-KDD is a benchmark dataset specifically designed to resolve inherent flaws present in the original KDD Cup 99 dataset. Key improvements include:
- **Zero Duplicate Records**: Eliminates bias toward frequent repeated network connections in train and test sets.
- **Balanced Difficulty Calibration**: Includes calibrated difficulty levels for evaluating model generalization.
- **Realistic Evaluation**: Test set includes unseen attack types not present in the training data, testing true zero-day detection capability.

---

## 2. Dataset Files & Splits

The raw dataset resides in the `NSL_Dataset/` directory:
- `Train.txt`: 125,973 network flow records used for training and preprocessor fitting.
- `Test.txt`: 22,544 connection records used strictly for out-of-sample evaluation.

---

## 3. Feature Definitions (41 Features + Target Columns)

Features fall into four distinct operational categories:

### A. Basic Connection Features (1–9)
1. `duration`: Length of connection in seconds (numeric).
2. `protocol_type`: Protocol type e.g. `tcp`, `udp`, `icmp` (categorical).
3. `service`: Network service e.g. `http`, `ftp`, `smtp`, `private`, `telnet` (categorical).
4. `flag`: Normal or error status of the connection e.g. `SF`, `S0`, `REJ` (categorical).
5. `src_bytes`: Bytes sent from source to destination (numeric).
6. `dst_bytes`: Bytes sent from destination to source (numeric).
7. `land`: 1 if connection is to/from the same host/port; 0 otherwise (binary).
8. `wrong_fragment`: Number of wrong fragments (numeric).
9. `urgent`: Number of urgent packets (numeric).

### B. Content Features (10–22)
10. `hot`: Number of "hot" indicators e.g. accessing system dirs (numeric).
11. `num_failed_logins`: Number of failed login attempts (numeric).
12. `logged_in`: 1 if successfully logged in; 0 otherwise (binary).
13. `num_compromised`: Number of compromised conditions (numeric).
14. `root_shell`: 1 if root shell is obtained; 0 otherwise (binary).
15. `su_attempted`: 1 if `su root` command attempted; 0 otherwise (binary).
16. `num_root`: Number of "root" accesses (numeric).
17. `num_file_creations`: Number of file creation operations (numeric).
18. `num_shells`: Number of shell prompts (numeric).
19. `num_access_files`: Number of operations on access control files (numeric).
20. `num_outbound_cmds`: Number of outbound commands in an ftp session (numeric).
21. `is_host_login`: 1 if the login belongs to the host list; 0 otherwise (binary).
22. `is_guest_login`: 1 if the login is a guest login; 0 otherwise (binary).

### C. Time-based Traffic Features (23–31)
23. `count`: Number of connections to the same host as the current connection in the past 2 seconds (numeric).
24. `srv_count`: Number of connections to the same service as the current connection in the past 2 seconds (numeric).
25. `serror_rate`: % of connections that have "SYN" errors (numeric).
26. `srv_serror_rate`: % of connections to the same service that have "SYN" errors (numeric).
27. `rerror_rate`: % of connections that have "REJ" errors (numeric).
28. `srv_rerror_rate`: % of connections to the same service that have "REJ" errors (numeric).
29. `same_srv_rate`: % of connections to the same service (numeric).
30. `diff_srv_rate`: % of connections to different services (numeric).
31. `srv_diff_host_rate`: % of connections to different hosts (numeric).

### D. Host-based Traffic Features (32–41)
32. `dst_host_count`: Count of connections having the same destination host (numeric).
33. `dst_host_srv_count`: Count of connections having the same destination host and service (numeric).
34. `dst_host_same_srv_rate`: Rate of connections to same service (numeric).
35. `dst_host_diff_srv_rate`: Rate of connections to different services (numeric).
36. `dst_host_same_src_port_rate`: Rate of connections from same source port (numeric).
37. `dst_host_srv_diff_host_rate`: Rate of connections to different hosts (numeric).
38. `dst_host_serror_rate`: Destination host SYN error rate (numeric).
39. `dst_host_srv_serror_rate`: Destination host service SYN error rate (numeric).
40. `dst_host_rerror_rate`: Destination host REJ error rate (numeric).
41. `dst_host_srv_rerror_rate`: Destination host service REJ error rate (numeric).

---

## 4. Attack Category Mapping Table

40 raw attack types map into 5 primary intrusion categories:

```python
{
    "normal": "Normal",
    
    # DOS
    "back": "DOS", "land": "DOS", "neptune": "DOS", "pod": "DOS",
    "smurf": "DOS", "teardrop": "DOS", "mailbomb": "DOS", "apache2": "DOS",
    "processtable": "DOS", "udpstorm": "DOS",
    
    # PROBE
    "ipsweep": "PROBE", "nmap": "PROBE", "portsweep": "PROBE",
    "satan": "PROBE", "mscan": "PROBE", "saint": "PROBE",
    
    # R2L
    "ftp_write": "R2L", "guess_passwd": "R2L", "imap": "R2L",
    "multihop": "R2L", "phf": "R2L", "spy": "R2L", "warezclient": "R2L",
    "warezmaster": "R2L", "sendmail": "R2L", "named": "R2L",
    "snmpgetattack": "R2L", "snmpguess": "R2L", "xlock": "R2L",
    "xsnoop": "R2L", "worm": "R2L", "httptunnel": "R2L",
    
    # U2R
    "buffer_overflow": "U2R", "loadmodule": "U2R", "perl": "U2R",
    "rootkit": "U2R", "xterm": "U2R", "ps": "U2R", "sqlattack": "U2R"
}
```
