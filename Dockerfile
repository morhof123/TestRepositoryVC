FROM python
COPY TestCombinedCapability.py /var
COPY requirements.txt /var
COPY virtualCapabilityServer.py /var
RUN python -m pip install -r /var/requirements.txt
EXPOSE 9999
CMD python /var/TestCombinedCapability.py