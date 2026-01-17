# Airflow Sensors

Sensors are a special type of Operator that wait for a certain condition to be met before proceeding. They continuously check (poke) for a condition at regular intervals.

## Overview

Sensors are useful for:
- Waiting for files to arrive
- Checking if external systems are ready
- Monitoring database conditions
- Waiting for time-based conditions
- Coordinating between DAGs

## Common Sensors

### 1. FileSensor

Wait for a file to appear in a specific location.

```python
from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    dag_id='file_sensor_example',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['sensor', 'file']
)

# Wait for file to appear
wait_for_file = FileSensor(
    task_id='wait_for_file',
    filepath='/path/to/file.csv',
    fs_conn_id='fs_default',
    poke_interval=30,  # Check every 30 seconds
    timeout=600,  # Timeout after 10 minutes
    mode='poke',  # or 'reschedule'
    dag=dag
)

def process_file(**kwargs):
    print("File found! Processing...")

process = PythonOperator(
    task_id='process_file',
    python_callable=process_file,
    dag=dag
)

wait_for_file >> process
```

### 2. S3KeySensor

Wait for a file to appear in S3.

```python
from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.operators.python import PythonOperator
from datetime import datetime

dag = DAG(
    dag_id='s3_sensor_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

wait_for_s3_file = S3KeySensor(
    task_id='wait_for_s3_file',
    bucket_name='my-bucket',
    bucket_key='data/{{ ds }}/file.csv',  # Templated path
    aws_conn_id='aws_default',
    poke_interval=60,
    timeout=3600,
    mode='reschedule',  # Free up worker slot while waiting
    dag=dag
)

def process_s3_file(**kwargs):
    print(f"Processing S3 file for {kwargs['ds']}")

process = PythonOperator(
    task_id='process_s3_file',
    python_callable=process_s3_file,
    dag=dag
)

wait_for_s3_file >> process
```

### 3. SqlSensor

Wait for a SQL query to return a result.

```python
from airflow import DAG
from airflow.providers.common.sql.sensors.sql import SqlSensor
from airflow.operators.python import PythonOperator
from datetime import datetime

dag = DAG(
    dag_id='sql_sensor_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@hourly',
    catchup=False
)

# Wait for records to be available
wait_for_data = SqlSensor(
    task_id='wait_for_data',
    conn_id='postgres_default',
    sql="SELECT COUNT(*) FROM orders WHERE date = '{{ ds }}'",
    success=lambda result: result[0][0] > 0,  # Success when count > 0
    poke_interval=60,
    timeout=3600,
    mode='reschedule',
    dag=dag
)

def process_data(**kwargs):
    print("Data is ready! Processing...")

process = PythonOperator(
    task_id='process_data',
    python_callable=process_data,
    dag=dag
)

wait_for_data >> process
```

### 4. ExternalTaskSensor

Wait for a task in another DAG to complete.

```python
from airflow import DAG
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

dag = DAG(
    dag_id='external_task_sensor_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

# Wait for another DAG's task to complete
wait_for_upstream_dag = ExternalTaskSensor(
    task_id='wait_for_upstream_dag',
    external_dag_id='upstream_dag',
    external_task_id='final_task',  # Specific task, or None for entire DAG
    allowed_states=['success'],
    failed_states=['failed', 'skipped'],
    execution_delta=timedelta(hours=1),  # Look for task 1 hour earlier
    poke_interval=60,
    timeout=3600,
    mode='reschedule',
    dag=dag
)

def process_after_upstream(**kwargs):
    print("Upstream DAG completed! Processing...")

process = PythonOperator(
    task_id='process_after_upstream',
    python_callable=process_after_upstream,
    dag=dag
)

wait_for_upstream_dag >> process
```

### 5. TimeSensor / TimeDeltaSensor

Wait until a specific time or time delta.

```python
from airflow import DAG
from airflow.sensors.time_sensor import TimeSensor
from airflow.sensors.time_delta import TimeDeltaSensor
from airflow.operators.python import PythonOperator
from datetime import datetime, time, timedelta

dag = DAG(
    dag_id='time_sensor_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

# Wait until specific time (e.g., 2:00 PM)
wait_until_2pm = TimeSensor(
    task_id='wait_until_2pm',
    target_time=time(14, 0, 0),  # 2:00 PM
    dag=dag
)

# Wait for a time delta from DAG start
wait_30_minutes = TimeDeltaSensor(
    task_id='wait_30_minutes',
    delta=timedelta(minutes=30),
    dag=dag
)

def process_after_time(**kwargs):
    print("Time condition met! Processing...")

process = PythonOperator(
    task_id='process_after_time',
    python_callable=process_after_time,
    dag=dag
)

wait_until_2pm >> wait_30_minutes >> process
```

### 6. HttpSensor

Wait for an HTTP endpoint to return a specific response.

```python
from airflow import DAG
from airflow.providers.http.sensors.http import HttpSensor
from airflow.operators.python import PythonOperator
from datetime import datetime

dag = DAG(
    dag_id='http_sensor_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@hourly',
    catchup=False
)

# Wait for API to be ready
wait_for_api = HttpSensor(
    task_id='wait_for_api',
    http_conn_id='http_default',
    endpoint='api/health',
    request_params={'check': 'status'},
    response_check=lambda response: response.json()['status'] == 'healthy',
    poke_interval=30,
    timeout=600,
    dag=dag
)

def call_api(**kwargs):
    print("API is healthy! Making request...")

call = PythonOperator(
    task_id='call_api',
    python_callable=call_api,
    dag=dag
)

wait_for_api >> call
```

## Custom Sensors

### Creating a Custom Sensor

```python
from airflow.sensors.base import BaseSensorOperator
from airflow.utils.decorators import apply_defaults
from typing import Any

class CustomDataSensor(BaseSensorOperator):
    """
    Custom sensor to check if data meets specific criteria
    """
    
    @apply_defaults
    def __init__(
        self,
        threshold: int,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.threshold = threshold
    
    def poke(self, context: Any) -> bool:
        """
        Check if condition is met
        Returns True if condition is met, False otherwise
        """
        # Your custom logic here
        current_value = self.get_current_value()
        
        self.log.info(f"Current value: {current_value}, Threshold: {self.threshold}")
        
        if current_value >= self.threshold:
            self.log.info("Threshold met!")
            return True
        else:
            self.log.info("Threshold not met, will retry...")
            return False
    
    def get_current_value(self) -> int:
        """
        Implement your logic to get current value
        """
        # Example: query database, check file size, call API, etc.
        return 100  # Placeholder

# Usage
dag = DAG(
    dag_id='custom_sensor_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

custom_sensor = CustomDataSensor(
    task_id='wait_for_threshold',
    threshold=100,
    poke_interval=60,
    timeout=3600,
    dag=dag
)
```

### Sensor with TaskFlow API (Airflow 2.5+)

```python
from airflow.decorators import dag, task
from airflow.sensors.base import PokeReturnValue
from datetime import datetime
import random

@dag(
    dag_id='sensor_taskflow',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def sensor_taskflow_example():
    
    @task.sensor(poke_interval=30, timeout=600, mode='poke')
    def wait_for_condition():
        """
        Custom sensor using TaskFlow API
        """
        # Your condition check logic
        condition_met = random.choice([True, False])
        
        if condition_met:
            return PokeReturnValue(is_done=True, xcom_value={'status': 'ready'})
        else:
            return PokeReturnValue(is_done=False)
    
    @task
    def process_data(sensor_result):
        print(f"Condition met! Result: {sensor_result}")
    
    result = wait_for_condition()
    process_data(result)

dag_instance = sensor_taskflow_example()
```

## Sensor Modes

### Poke Mode (Default)

```python
sensor = FileSensor(
    task_id='poke_sensor',
    filepath='/path/to/file.csv',
    mode='poke',  # Occupies worker slot continuously
    poke_interval=60,
    dag=dag
)
```

**Characteristics:**
- Occupies a worker slot continuously
- Good for short waits
- Lower latency
- Can exhaust worker slots if many sensors are waiting

### Reschedule Mode

```python
sensor = FileSensor(
    task_id='reschedule_sensor',
    filepath='/path/to/file.csv',
    mode='reschedule',  # Frees worker slot between checks
    poke_interval=300,
    dag=dag
)
```

**Characteristics:**
- Frees worker slot between checks
- Better for long waits
- More efficient resource usage
- Slightly higher latency

## Best Practices

### 1. Choose Appropriate Mode

```python
# ✅ Good: Use reschedule for long waits
long_wait_sensor = S3KeySensor(
    task_id='wait_for_large_file',
    bucket_name='my-bucket',
    bucket_key='large_file.csv',
    mode='reschedule',  # Free up worker
    poke_interval=300,  # Check every 5 minutes
    timeout=86400,  # 24 hour timeout
    dag=dag
)

# ✅ Good: Use poke for short waits
short_wait_sensor = SqlSensor(
    task_id='wait_for_quick_update',
    conn_id='postgres_default',
    sql="SELECT COUNT(*) FROM quick_table",
    mode='poke',  # Keep worker
    poke_interval=10,  # Check every 10 seconds
    timeout=300,  # 5 minute timeout
    dag=dag
)
```

### 2. Set Appropriate Timeouts

```python
# ✅ Good: Set reasonable timeout
sensor = FileSensor(
    task_id='wait_for_file',
    filepath='/path/to/file.csv',
    timeout=3600,  # 1 hour timeout
    poke_interval=60,
    dag=dag
)

# ❌ Bad: No timeout or too long
sensor = FileSensor(
    task_id='wait_forever',
    filepath='/path/to/file.csv',
    timeout=None,  # Will wait forever!
    dag=dag
)
```

### 3. Use Soft Fail for Optional Dependencies

```python
# Optional dependency - don't fail DAG if not met
optional_sensor = ExternalTaskSensor(
    task_id='wait_for_optional_task',
    external_dag_id='optional_dag',
    external_task_id='optional_task',
    soft_fail=True,  # Mark as skipped instead of failed
    timeout=600,
    dag=dag
)
```

### 4. Optimize Poke Interval

```python
# ✅ Good: Balance between responsiveness and resource usage
sensor = S3KeySensor(
    task_id='balanced_sensor',
    bucket_name='my-bucket',
    bucket_key='file.csv',
    poke_interval=60,  # Check every minute
    mode='reschedule',
    dag=dag
)

# ❌ Bad: Too frequent poking
sensor = S3KeySensor(
    task_id='aggressive_sensor',
    bucket_name='my-bucket',
    bucket_key='file.csv',
    poke_interval=1,  # Checking every second!
    mode='poke',
    dag=dag
)
```

## Advanced Patterns

### 1. Multiple File Sensors

```python
from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.operators.python import PythonOperator
from datetime import datetime

dag = DAG(
    dag_id='multiple_file_sensors',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

files_to_wait = ['file1.csv', 'file2.csv', 'file3.csv']

def process_all_files(**kwargs):
    print("All files arrived! Processing...")

process = PythonOperator(
    task_id='process_all_files',
    python_callable=process_all_files,
    dag=dag
)

# Wait for all files in parallel
for file in files_to_wait:
    sensor = FileSensor(
        task_id=f'wait_for_{file.replace(".", "_")}',
        filepath=f'/data/{file}',
        poke_interval=60,
        timeout=3600,
        mode='reschedule',
        dag=dag
    )
    sensor >> process
```

### 2. Sensor with Retry Logic

```python
from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from datetime import datetime, timedelta

dag = DAG(
    dag_id='sensor_with_retries',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

sensor = FileSensor(
    task_id='wait_for_file_with_retries',
    filepath='/path/to/file.csv',
    poke_interval=60,
    timeout=600,  # 10 minute timeout per attempt
    mode='reschedule',
    retries=3,  # Retry 3 times if timeout
    retry_delay=timedelta(minutes=5),  # Wait 5 minutes between retries
    dag=dag
)
```

### 3. Conditional Sensor Execution

```python
from airflow.decorators import dag, task
from airflow.sensors.filesystem import FileSensor
from datetime import datetime

@dag(
    dag_id='conditional_sensor',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def conditional_sensor_example():
    
    @task.branch
    def check_if_sensor_needed():
        # Logic to determine if we need to wait
        need_to_wait = True  # Your logic here
        
        if need_to_wait:
            return 'wait_for_file'
        else:
            return 'skip_wait'
    
    @task
    def skip_wait():
        print("No need to wait, proceeding...")
    
    @task
    def process_file():
        print("Processing file...")
    
    branch = check_if_sensor_needed()
    
    wait = FileSensor(
        task_id='wait_for_file',
        filepath='/path/to/file.csv',
        poke_interval=60,
        timeout=600,
        mode='reschedule'
    )
    
    skip = skip_wait()
    process = process_file()
    
    branch >> [wait, skip]
    [wait, skip] >> process

dag_instance = conditional_sensor_example()
```

## Troubleshooting

### Sensor Timing Out

```python
# Increase timeout and adjust poke interval
sensor = FileSensor(
    task_id='patient_sensor',
    filepath='/path/to/file.csv',
    poke_interval=120,  # Check less frequently
    timeout=7200,  # Longer timeout (2 hours)
    mode='reschedule',
    dag=dag
)
```

### Too Many Sensors Blocking Workers

```python
# Use reschedule mode to free up workers
sensor = S3KeySensor(
    task_id='efficient_sensor',
    bucket_name='my-bucket',
    bucket_key='file.csv',
    mode='reschedule',  # Free worker between checks
    poke_interval=300,
    dag=dag
)
```

### Debugging Sensor Logic

```python
from airflow.sensors.base import BaseSensorOperator

class DebugSensor(BaseSensorOperator):
    def poke(self, context):
        # Add detailed logging
        self.log.info("Checking condition...")
        self.log.info(f"Context: {context}")
        
        result = self.check_condition()
        self.log.info(f"Condition result: {result}")
        
        return result
    
    def check_condition(self):
        # Your condition logic
        return True
```

## Complete Example: Data Pipeline with Sensors

```python
from airflow.decorators import dag, task
from airflow.sensors.filesystem import FileSensor
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.sensors.external_task import ExternalTaskSensor
from datetime import datetime, timedelta

@dag(
    dag_id='complete_sensor_pipeline',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['sensor', 'pipeline']
)
def sensor_pipeline():
    
    # Wait for upstream DAG to complete
    wait_upstream = ExternalTaskSensor(
        task_id='wait_for_upstream_dag',
        external_dag_id='data_extraction_dag',
        external_task_id='extract_complete',
        allowed_states=['success'],
        execution_delta=timedelta(hours=0),
        poke_interval=60,
        timeout=3600,
        mode='reschedule'
    )
    
    # Wait for local file
    wait_local_file = FileSensor(
        task_id='wait_for_local_file',
        filepath='/data/{{ ds }}/input.csv',
        poke_interval=60,
        timeout=1800,
        mode='reschedule'
    )
    
    # Wait for S3 file
    wait_s3_file = S3KeySensor(
        task_id='wait_for_s3_file',
        bucket_name='my-data-bucket',
        bucket_key='raw/{{ ds }}/data.parquet',
        aws_conn_id='aws_default',
        poke_interval=120,
        timeout=3600,
        mode='reschedule'
    )
    
    @task
    def process_data():
        print("All conditions met! Processing data...")
        return "Processing complete"
    
    @task
    def send_notification(result):
        print(f"Pipeline complete: {result}")
    
    # Define dependencies
    [wait_upstream, wait_local_file, wait_s3_file] >> process_data() >> send_notification()

dag_instance = sensor_pipeline()
```

## Additional Resources

- [Sensors Documentation](https://airflow.apache.org/docs/apache-airflow/stable/concepts/sensors.html)
- [Deferrable Operators](https://airflow.apache.org/docs/apache-airflow/stable/concepts/deferring.html)
- [Provider Sensors](https://airflow.apache.org/docs/apache-airflow-providers/)