FROM python:3.12-slim
RUN addgroup --system app && adduser --system --uid 10001 --ingroup app app
WORKDIR /app
COPY app/service.py .
USER 10001
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "service.py"]
