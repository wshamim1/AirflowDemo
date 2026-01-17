# XCom (Cross-Communication) in Airflow

XCom (short for "cross-communication") allows tasks to exchange messages or small amounts of data between each other.

## Overview

XComs are a mechanism that let tasks talk to each other. They are defined by a key, value, and timestamp, and are stored in Airflow's metadata database.

## Basic Usage

### Pushing Values to XCom

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def push_function(**kwargs):
    # Method 1: Return value (automatically pushed to XCom)
    return "This value is automatically pushed to XCom"

def push_explicit(**kwargs):
    # Method 2: Explicit push using task_instance
    ti = kwargs['ti']
    ti.xcom_push(key='my_key', value='My custom value')
    ti.xcom_push(key='another_key', value={'data': 'dictionary'})

dag = DAG(
    dag_id='xcom_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

push_task = PythonOperator(
    task_id='push_task',
    python_callable=push_function,
    dag=dag
)

push_explicit_task = PythonOperator(
    task_id='push_explicit',
    python_callable=push_explicit,
    dag=dag
)
```

### Pulling Values from XCom

```python
def pull_function(**kwargs):
    ti = kwargs['ti']
    
    # Pull the return value from push_task
    value = ti.xcom_pull(task_ids='push_task')
    print(f"Pulled value: {value}")
    
    # Pull specific key from push_explicit
    custom_value = ti.xcom_pull(task_ids='push_explicit', key='my_key')
    print(f"Custom value: {custom_value}")
    
    # Pull from multiple tasks
    values = ti.xcom_pull(task_ids=['push_task', 'push_explicit'])
    print(f"Multiple values: {values}")

pull_task = PythonOperator(
    task_id='pull_task',
    python_callable=pull_function,
    dag=dag
)

push_task >> pull_task
push_explicit_task >> pull_task
```

## TaskFlow API (Airflow 2.0+)

The TaskFlow API makes XCom usage much simpler and more Pythonic.

### Basic Example

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='xcom_taskflow',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def xcom_taskflow_example():
    
    @task
    def extract_data():
        """Extract data and return it"""
        return {'users': 100, 'orders': 500}
    
    @task
    def transform_data(data: dict):
        """Transform the data"""
        transformed = {
            'total_users': data['users'],
            'total_orders': data['orders'],
            'avg_orders_per_user': data['orders'] / data['users']
        }
        return transformed
    
    @task
    def load_data(data: dict):
        """Load the transformed data"""
        print(f"Loading data: {data}")
        return "Data loaded successfully"
    
    # Data flows automatically through XCom
    raw_data = extract_data()
    transformed_data = transform_data(raw_data)
    load_data(transformed_data)

dag_instance = xcom_taskflow_example()
```

### Multiple Return Values

```python
from airflow.decorators import dag, task
from datetime import datetime
from typing import Tuple

@dag(
    dag_id='xcom_multiple_returns',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def multiple_returns_example():
    
    @task
    def process_data() -> Tuple[dict, list, int]:
        """Return multiple values"""
        summary = {'status': 'success'}
        items = ['item1', 'item2', 'item3']
        count = 3
        return summary, items, count
    
    @task
    def use_summary(summary: dict):
        print(f"Summary: {summary}")
    
    @task
    def use_items(items: list):
        print(f"Items: {items}")
    
    @task
    def use_count(count: int):
        print(f"Count: {count}")
    
    # Unpack multiple return values
    summary, items, count = process_data()
    
    use_summary(summary)
    use_items(items)
    use_count(count)

dag_instance = multiple_returns_example()
```

## Advanced Patterns

### 1. Conditional XCom Usage

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='conditional_xcom',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def conditional_xcom_example():
    
    @task
    def check_data_quality():
        """Check data quality and return status"""
        quality_score = 0.95  # Example score
        
        if quality_score > 0.9:
            return {'status': 'good', 'score': quality_score}
        else:
            return {'status': 'poor', 'score': quality_score}
    
    @task.branch
    def decide_path(quality_result: dict):
        """Branch based on data quality"""
        if quality_result['status'] == 'good':
            return 'process_data'
        else:
            return 'send_alert'
    
    @task
    def process_data():
        print("Processing high-quality data")
    
    @task
    def send_alert():
        print("Sending alert for poor data quality")
    
    quality = check_data_quality()
    branch = decide_path(quality)
    
    branch >> [process_data(), send_alert()]

dag_instance = conditional_xcom_example()
```

### 2. Aggregating XCom from Multiple Tasks

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='aggregate_xcom',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def aggregate_xcom_example():
    
    @task
    def process_source_a():
        return {'source': 'A', 'count': 100}
    
    @task
    def process_source_b():
        return {'source': 'B', 'count': 200}
    
    @task
    def process_source_c():
        return {'source': 'C', 'count': 150}
    
    @task
    def aggregate_results(results: list):
        """Aggregate results from multiple sources"""
        total = sum(r['count'] for r in results)
        print(f"Total count from all sources: {total}")
        return {'total': total, 'sources': len(results)}
    
    # Process multiple sources in parallel
    result_a = process_source_a()
    result_b = process_source_b()
    result_c = process_source_c()
    
    # Aggregate all results
    aggregate_results([result_a, result_b, result_c])

dag_instance = aggregate_xcom_example()
```

### 3. XCom with Custom Objects

```python
from airflow.decorators import dag, task
from datetime import datetime
from dataclasses import dataclass
import json

@dataclass
class DataReport:
    date: str
    records_processed: int
    errors: int
    status: str
    
    def to_dict(self):
        return {
            'date': self.date,
            'records_processed': self.records_processed,
            'errors': self.errors,
            'status': self.status
        }

@dag(
    dag_id='xcom_custom_objects',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def custom_objects_example():
    
    @task
    def generate_report():
        """Generate a report object"""
        report = DataReport(
            date='2024-01-01',
            records_processed=1000,
            errors=5,
            status='completed'
        )
        # Convert to dict for XCom serialization
        return report.to_dict()
    
    @task
    def analyze_report(report_dict: dict):
        """Analyze the report"""
        error_rate = report_dict['errors'] / report_dict['records_processed']
        print(f"Error rate: {error_rate:.2%}")
        
        if error_rate > 0.01:
            return "High error rate detected"
        else:
            return "Error rate acceptable"
    
    report = generate_report()
    analyze_report(report)

dag_instance = custom_objects_example()
```

## Traditional Operator XCom Usage

### Pulling XCom in Templates

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime

def generate_filename(**kwargs):
    return f"data_{kwargs['ds']}.csv"

dag = DAG(
    dag_id='xcom_templates',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

generate_task = PythonOperator(
    task_id='generate_filename',
    python_callable=generate_filename,
    dag=dag
)

# Use XCom value in Bash command template
process_task = BashOperator(
    task_id='process_file',
    bash_command='echo "Processing {{ ti.xcom_pull(task_ids="generate_filename") }}"',
    dag=dag
)

generate_task >> process_task
```

## Best Practices

### 1. Size Limitations

```python
# ❌ Bad: Storing large data in XCom
@task
def bad_practice():
    large_dataframe = load_huge_dataset()  # Don't do this!
    return large_dataframe

# ✅ Good: Store reference or summary
@task
def good_practice():
    large_dataframe = load_huge_dataset()
    # Save to external storage
    file_path = save_to_s3(large_dataframe)
    # Return only the reference
    return {'file_path': file_path, 'row_count': len(large_dataframe)}
```

### 2. Type Hints

```python
from typing import Dict, List

@task
def typed_function() -> Dict[str, int]:
    """Use type hints for better code clarity"""
    return {'count': 100, 'errors': 5}

@task
def process_typed_data(data: Dict[str, int]) -> List[str]:
    """Type hints make data flow clear"""
    return [f"{k}: {v}" for k, v in data.items()]
```

### 3. Error Handling

```python
@task
def safe_xcom_pull(**kwargs):
    ti = kwargs['ti']
    
    # Handle missing XCom gracefully
    value = ti.xcom_pull(task_ids='upstream_task', default='default_value')
    
    if value is None:
        print("No value found, using default")
        value = 'default_value'
    
    return value
```

## XCom Backend Configuration

### Custom XCom Backend

For large XComs, configure a custom backend in `airflow.cfg`:

```ini
[core]
xcom_backend = airflow.providers.amazon.aws.xcom_backends.s3.S3XComBackend

[aws]
xcom_s3_bucket = my-xcom-bucket
xcom_s3_key_prefix = xcom/
```

## Limitations and Considerations

1. **Size Limit**: Default XCom size limit is typically 48KB (varies by database)
2. **Serialization**: Only JSON-serializable objects work by default
3. **Performance**: Large XComs can slow down the metadata database
4. **Cleanup**: XComs are not automatically cleaned up (configure retention)

## Debugging XComs

### View XComs in UI

1. Navigate to Admin → XComs in Airflow UI
2. Filter by DAG ID, Task ID, or Execution Date
3. View key-value pairs

### Programmatic Access

```python
from airflow.models import XCom

def debug_xcoms(**kwargs):
    ti = kwargs['ti']
    
    # Get all XComs for this DAG run
    xcoms = XCom.get_many(
        execution_date=ti.execution_date,
        dag_ids=[ti.dag_id]
    )
    
    for xcom in xcoms:
        print(f"Task: {xcom.task_id}, Key: {xcom.key}, Value: {xcom.value}")
```

## Complete Example: ETL Pipeline with XCom

```python
from airflow.decorators import dag, task
from datetime import datetime
from typing import Dict, List

@dag(
    dag_id='etl_with_xcom',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['etl', 'xcom']
)
def etl_pipeline():
    
    @task
    def extract() -> Dict[str, any]:
        """Extract data from source"""
        print("Extracting data...")
        return {
            'records': 1000,
            'source': 'database_a',
            'timestamp': datetime.now().isoformat()
        }
    
    @task
    def validate(extract_result: Dict) -> Dict[str, any]:
        """Validate extracted data"""
        print(f"Validating {extract_result['records']} records...")
        
        validation_result = {
            'valid_records': extract_result['records'] - 10,
            'invalid_records': 10,
            'validation_passed': True
        }
        
        return {**extract_result, **validation_result}
    
    @task
    def transform(validated_data: Dict) -> Dict[str, any]:
        """Transform validated data"""
        print(f"Transforming {validated_data['valid_records']} records...")
        
        return {
            'transformed_records': validated_data['valid_records'],
            'transformation_time': '2.5s',
            'source': validated_data['source']
        }
    
    @task
    def load(transformed_data: Dict) -> str:
        """Load transformed data"""
        print(f"Loading {transformed_data['transformed_records']} records...")
        return f"Successfully loaded {transformed_data['transformed_records']} records"
    
    @task
    def send_report(load_result: str, extract_result: Dict, transform_result: Dict):
        """Send completion report"""
        report = f"""
        ETL Pipeline Completed
        =====================
        Source: {extract_result['source']}
        Extracted: {extract_result['records']} records
        Transformed: {transform_result['transformed_records']} records
        Result: {load_result}
        """
        print(report)
    
    # Define pipeline flow
    extract_result = extract()
    validated_data = validate(extract_result)
    transformed_data = transform(validated_data)
    load_result = load(transformed_data)
    send_report(load_result, extract_result, transformed_data)

dag_instance = etl_pipeline()
```

## Additional Resources

- [XCom Documentation](https://airflow.apache.org/docs/apache-airflow/stable/concepts/xcoms.html)
- [TaskFlow API](https://airflow.apache.org/docs/apache-airflow/stable/tutorial_taskflow_api.html)
- [Custom XCom Backends](https://airflow.apache.org/docs/apache-airflow/stable/concepts/xcoms.html#custom-xcom-backends)