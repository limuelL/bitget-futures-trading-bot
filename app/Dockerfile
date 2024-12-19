FROM public.ecr.aws/lambda/python:3.10

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# upgrade pip
RUN python3 -m pip install --upgrade pip

# RUN pip install -r requirements.txt
RUN pip install --default-timeout=1000 -r requirements.txt

# Copy function code
COPY . ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "main.start_trade" ]