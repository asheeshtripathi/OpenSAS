# Open Source Spectrum Access System (SAS)
## What is this?
This is the code for the Virginia Tech Open Source SAS (VT OpenSAS) and VT SAS client. The role of the SAS is to allow
for remote and autonomous operation of the USRPs in Kelly Hall. The SAS is
to adhere to WinnForum and FCC regulations on SAS operations.

## Getting started
Please refer to https://github.com/CCI-NextG-Testbed/OpenSASDocker for the dockerfile to create a image for this repository. The dockerfile also clones the 
OpenSAS-dashboard repo and runs it.

The dockerfile is the easiest way to get started.

## File Structure
### Core
The Core/ folder contains everything required to launch the SAS Core
Server. This is the true SAS. It may have connections to N number of socketio
clients. Regardess of your institution, this contians the code that is of
primary interet for SAS researchers.

An example of starting up the SAS server server.py:
```python3 server.py```

The CBSDs can access the SAS via the following URL endpoints:

http://localhost:1443/sas-api/registration

http://localhost:1443/sas-api/spectrumInquiry

http://localhost:1443/sas-api/grant

http://localhost:1443/sas-api/heartbeat

http://localhost:1443/sas-api/relinquishment

http://localhost:1443/sas-api/deregistration


