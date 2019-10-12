FROM python:3.7-slim
WORKDIR /app
COPY . /app
RUN pip install Flask
RUN pip install Pillow
RUN pip install tensorflow==1.14
EXPOSE 80
CMD ["python", "pictures.py"]

