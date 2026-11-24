FROM python:3.12-slim
RUN addgroup --system app && adduser --system --ingroup app app
WORKDIR /app
COPY app/service.py .
USER app
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "service.py"]
