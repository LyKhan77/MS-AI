gspe-ai3@gspe-ai3-MS-7E32:~/project_cv$ nvidia-smi
Fri Dec 19 09:05:54 2025  
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.95.05 Driver Version: 580.95.05 CUDA Version: 13.0 |
+-----------------------------------------+------------------------+----------------------+
| GPU Name Persistence-M | Bus-Id Disp.A | Volatile Uncorr. ECC |
| Fan Temp Perf Pwr:Usage/Cap | Memory-Usage | GPU-Util Compute M. |
| | | MIG M. |
|=========================================+========================+======================|
| 0 NVIDIA GeForce RTX 5080 Off | 00000000:02:00.0 Off | N/A |
| 0% 60C P1 55W / 360W | 1341MiB / 16303MiB | 13% Default |
| | | N/A |
+-----------------------------------------+------------------------+----------------------+
| 1 NVIDIA GeForce RTX 4090 Off | 00000000:83:00.0 Off | Off |
| 30% 35C P2 76W / 450W | 2783MiB / 24564MiB | 18% Default |
| | | N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes: |
| GPU GI CI PID Type Process name GPU Memory |
| ID ID Usage |
|=========================================================================================|
| 0 N/A N/A 3422 G /usr/lib/xorg/Xorg 4MiB |
| 0 N/A N/A 3674006 C python 1318MiB |
| 1 N/A N/A 3422 G /usr/lib/xorg/Xorg 4MiB |
| 1 N/A N/A 1159424 C ...tyRecognition/venv/bin/python 686MiB |
| 1 N/A N/A 1182904 C ...tyRecognition/venv/bin/python 686MiB |
| 1 N/A N/A 1183342 C ...tyRecognition/venv/bin/python 686MiB |
| 1 N/A N/A 1183803 C ...tyRecognition/venv/bin/python 686MiB |
+-----------------------------------------------------------------------------------------+
gspe-ai3@gspe-ai3-MS-7E32:~/project_cv$ nvcc --version
nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2025 NVIDIA Corporation
Built on Wed_Jan_15_19:20:09_PST_2025
Cuda compilation tools, release 12.8, V12.8.61
Build cuda_12.8.r12.8/compiler.35404655_0
