# Airflow Operators Guide

Operators are the building blocks of Airflow DAGs. They define the individual tasks that make up your workflow.

## Overview

Operators determine what actually gets done in a task. Airflow provides many built-in operators, and you can also create custom ones.

## Common Operators

### 1. PythonOperator

Executes a Python callable (function).

#### Basic Usage

```python
from airflow.operators.python import PythonOperator
from airflow import DAG
from datetime import datetime

def my_python_function(**kwargs):
    print("Hello from Python!")
    return "Success"

dag = DAG(
    dag_id='python_operator_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

python_task = PythonOperator(
    task_id='run_python_function',
    python_callable=my_python_function,
    dag=dag
)
```

#### With Arguments

```python
def process_data(name, value, **kwargs):
    print(f"Processing {name} with value {value}")
    return f"Processed {name}"

python_task_with_args = PythonOperator(
    task_id='process_with_args',
    python_callable=process_data,
    op_kwargs={'name': 'dataset_1', 'value': 100},
    dag=dag
)
```

#### Modern Alternative: TaskFlow API (Airflow 2.0+)

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='taskflow_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def my_taskflow_dag():
    
    @task
    def my_python_function():
        print("Hello from TaskFlow!")
        return "Success"
    
    @task
    def process_data(name: str, value: int):
        print(f"Processing {name} with value {value}")
        return f"Processed {name}"
    
    # Call the tasks
    result1 = my_python_function()
    result2 = process_data(name='dataset_1', value=100)
    
    result1 >> result2

# Instantiate the DAG
dag_instance = my_taskflow_dag()
```

---

### 2. BashOperator

Executes bash commands or scripts.

#### Basic Command

```python
from airflow.operators.bash import BashOperator
from airflow import DAG
from datetime import datetime

dag = DAG(
    dag_id='bash_operator_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

# Simple bash command
print_date = BashOperator(
    task_id='print_date',
    bash_command='date',
    dag=dag
)

# Multiple commands
multi_command = BashOperator(
    task_id='multi_command',
    bash_command='echo "Starting..." && date && echo "Done!"',
    dag=dag
)
```

#### Execute Shell Script

```python
# Execute a shell script
run_script = BashOperator(
    task_id='run_shell_script',
    bash_command='/path/to/your/script.sh',
    dag=dag
)

# Execute script with arguments
run_script_with_args = BashOperator(
    task_id='run_script_with_args',
    bash_command='/path/to/script.sh {{ ds }} {{ params.environment }}',
    params={'environment': 'production'},
    dag=dag
)
```

#### Change Directory and Execute

```python
# Run command in specific directory
run_in_directory = BashOperator(
    task_id='run_in_directory',
    bash_command='cd /path/to/directory && python process.py',
    dag=dag
)
```

#### With Environment Variables

```python
# Set environment variables
bash_with_env = BashOperator(
    task_id='bash_with_env',
    bash_command='echo "Environment: $ENVIRONMENT"',
    env={'ENVIRONMENT': 'production', 'LOG_LEVEL': 'INFO'},
    dag=dag
)
```

---

### 3. DummyOperator (EmptyOperator in Airflow 2.4+)

A placeholder operator that does nothing. Useful for organizing DAG structure.

```python
from airflow.operators.dummy import DummyOperator
# Or for Airflow 2.4+:
# from airflow.operators.empty import EmptyOperator

dag = DAG(
    dag_id='dummy_operator_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

start = DummyOperator(task_id='start', dag=dag)
end = DummyOperator(task_id='end', dag=dag)

# Use for grouping or organizing workflow
section_1_start = DummyOperator(task_id='section_1_start', dag=dag)
section_1_end = DummyOperator(task_id='section_1_end', dag=dag)
```

---

## Other Common Operators

### EmailOperator

```python
from airflow.operators.email import EmailOperator

send_email = EmailOperator(
    task_id='send_email',
    to='user@example.com',
    subject='Airflow Alert',
    html_content='<h3>Task completed successfully!</h3>',
    dag=dag
)
```

### SQLOperator

```python
from airflow.providers.postgres.operators.postgres import PostgresOperator

run_sql = PostgresOperator(
    task_id='run_sql_query',
    postgres_conn_id='postgres_default',
    sql='SELECT * FROM users WHERE created_date = {{ ds }}',
    dag=dag
)
```

### HttpOperator

```python
from airflow.providers.http.operators.http import SimpleHttpOperator

call_api = SimpleHttpOperator(
    task_id='call_api',
    http_conn_id='http_default',
    endpoint='api/v1/data',
    method='GET',
    headers={'Content-Type': 'application/json'},
    dag=dag
)
```

---

## Operator Comparison

| Operator | Use Case | Airflow Version |
|----------|----------|-----------------|
| PythonOperator | Execute Python functions | All versions |
| @task decorator | Execute Python functions (cleaner syntax) | 2.0+ |
| BashOperator | Execute bash commands/scripts | All versions |
| DummyOperator | Placeholder/organization | All versions |
| EmptyOperator | Placeholder/organization (renamed) | 2.4+ |

---

## Best Practices

1. **Use TaskFlow API**: For Airflow 2.0+, prefer the `@task` decorator over PythonOperator for cleaner code.

2. **Idempotency**: Ensure your operators can be safely re-run without side effects.

3. **Resource Management**: Set appropriate resources (memory, CPU) for operators that need them.

4. **Error Handling**: Implement proper error handling in your Python callables.

5. **Logging**: Use Airflow's logging instead of print statements:
   ```python
   from airflow.utils.log.logging_mixin import LoggingMixin
   
   def my_function(**kwargs):
       logger = LoggingMixin().log
       logger.info("This is a log message")
   ```

6. **Connection Management**: Use Airflow Connections for external systems instead of hardcoding credentials.

---

## Complete Example

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    dag_id='operators_complete_example',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['example', 'operators']
)

def extract_data(**kwargs):
    print("Extracting data...")
    return "data_extracted"

def transform_data(**kwargs):
    print("Transforming data...")
    return "data_transformed"

# Define tasks
start = DummyOperator(task_id='start', dag=dag)

extract = PythonOperator(
    task_id='extract',
    python_callable=extract_data,
    dag=dag
)

transform = PythonOperator(
    task_id='transform',
    python_callable=transform_data,
    dag=dag
)

load = BashOperator(
    task_id='load',
    bash_command='echo "Loading data to warehouse..."',
    dag=dag
)

end = DummyOperator(task_id='end', dag=dag)

# Set dependencies
start >> extract >> transform >> load >> end
```

---

## Additional Resources

- [Airflow Operators Documentation](https://airflow.apache.org/docs/apache-airflow/stable/concepts/operators.html)
- [Provider Packages](https://airflow.apache.org/docs/apache-airflow-providers/)
- [Custom Operators](https://airflow.apache.org/docs/apache-airflow/stable/howto/custom-operator.html)
