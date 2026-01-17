# TriggerDagRunOperator

The `TriggerDagRunOperator` allows you to trigger another DAG from within a DAG, enabling complex workflow orchestration and DAG chaining.

## Overview

This operator is useful when you need to:
- Chain multiple DAGs together
- Trigger a DAG based on conditions in another DAG
- Pass data between DAGs
- Create modular, reusable workflows

## Basic Example

### Step 1: Create the Target DAG (to be triggered)

Create a file `triggered_dag.py`:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
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

# Target DAG - will be triggered by another DAG
dag = DAG(
    dag_id='triggered_dag',
    default_args=default_args,
    schedule_interval=None,  # Only triggered manually or by TriggerDagRunOperator
    catchup=False,
    tags=['triggered', 'example']
)

def process_triggered_data(**kwargs):
    """
    Process data received from the triggering DAG
    """
    # Access data passed from triggering DAG
    dag_run = kwargs.get('dag_run')
    if dag_run and dag_run.conf:
        message = dag_run.conf.get('message', 'No message')
        print(f"Received message: {message}")
    else:
        print("No configuration data received")
    
    return "Processing complete"

with dag:
    start = DummyOperator(task_id='start')
    
    process = PythonOperator(
        task_id='process_data',
        python_callable=process_triggered_data,
        provide_context=True
    )
    
    task_three = DummyOperator(task_id='three')
    task_four = DummyOperator(task_id='four')
    task_five = DummyOperator(task_id='five')
    task_six = DummyOperator(task_id='six')
    end = DummyOperator(task_id='end')
    
    start >> process >> task_three >> task_four >> task_five >> task_six >> end
```

### Step 2: Create the Triggering DAG

Create a file `triggering_dag.py`:

```python
from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
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

# Triggering DAG - runs on schedule and triggers another DAG
dag = DAG(
    dag_id='triggering_dag',
    default_args=default_args,
    schedule_interval='@hourly',
    catchup=False,
    tags=['trigger', 'example']
)

with dag:
    start = DummyOperator(task_id='start')
    
    # Trigger another DAG
    trigger_task = TriggerDagRunOperator(
        task_id='trigger_target_dag',
        trigger_dag_id='triggered_dag',  # ID of the DAG to trigger
        conf={'message': 'Hello from triggering DAG!'},  # Pass data to triggered DAG
        wait_for_completion=False,  # Don't wait for triggered DAG to complete
        poke_interval=30,  # Check status every 30 seconds (if wait_for_completion=True)
        reset_dag_run=True,  # Clear existing DAG run if it exists
        execution_date='{{ ds }}',  # Use same execution date
    )
    
    end = DummyOperator(task_id='end')
    
    start >> trigger_task >> end
```

![TriggerDagRun Example](images/triggerDagRun.png)

---

## Advanced Examples

### 1. Conditional Triggering

Trigger a DAG only if certain conditions are met:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime

def check_condition(**kwargs):
    """
    Determine whether to trigger the target DAG
    """
    # Your condition logic here
    should_trigger = True  # Replace with actual condition
    
    if should_trigger:
        return 'trigger_dag'
    else:
        return 'skip_trigger'

dag = DAG(
    dag_id='conditional_trigger',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

with dag:
    start = DummyOperator(task_id='start')
    
    check = BranchPythonOperator(
        task_id='check_condition',
        python_callable=check_condition,
        provide_context=True
    )
    
    trigger = TriggerDagRunOperator(
        task_id='trigger_dag',
        trigger_dag_id='triggered_dag',
        conf={'triggered_by': 'conditional_trigger'}
    )
    
    skip = DummyOperator(task_id='skip_trigger')
    end = DummyOperator(task_id='end', trigger_rule='none_failed_min_one_success')
    
    start >> check >> [trigger, skip] >> end
```

### 2. Wait for Completion

Wait for the triggered DAG to complete before continuing:

```python
from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python import PythonOperator
from datetime import datetime

def process_results(**kwargs):
    print("Triggered DAG completed, processing results...")

dag = DAG(
    dag_id='trigger_and_wait',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

with dag:
    trigger = TriggerDagRunOperator(
        task_id='trigger_and_wait',
        trigger_dag_id='triggered_dag',
        wait_for_completion=True,  # Wait for triggered DAG to complete
        poke_interval=30,  # Check every 30 seconds
        allowed_states=['success'],  # Only continue if triggered DAG succeeds
        failed_states=['failed'],  # Fail this task if triggered DAG fails
    )
    
    process = PythonOperator(
        task_id='process_results',
        python_callable=process_results
    )
    
    trigger >> process
```

### 3. Dynamic Configuration

Pass dynamic data to the triggered DAG:

```python
from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import json

def prepare_config(**kwargs):
    """
    Prepare configuration data for the triggered DAG
    """
    config = {
        'source': 'database_a',
        'target': 'warehouse_b',
        'date': kwargs['ds'],
        'batch_size': 1000
    }
    return config

dag = DAG(
    dag_id='dynamic_trigger',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

with dag:
    prepare = PythonOperator(
        task_id='prepare_config',
        python_callable=prepare_config
    )
    
    trigger = TriggerDagRunOperator(
        task_id='trigger_with_config',
        trigger_dag_id='triggered_dag',
        conf="{{ task_instance.xcom_pull(task_ids='prepare_config') }}"
    )
    
    prepare >> trigger
```

### 4. Multiple DAG Triggers

Trigger multiple DAGs in parallel:

```python
from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime

dag = DAG(
    dag_id='multi_trigger',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

target_dags = ['dag_a', 'dag_b', 'dag_c']

with dag:
    start = DummyOperator(task_id='start')
    end = DummyOperator(task_id='end')
    
    # Create trigger tasks for each target DAG
    trigger_tasks = []
    for target_dag in target_dags:
        trigger = TriggerDagRunOperator(
            task_id=f'trigger_{target_dag}',
            trigger_dag_id=target_dag,
            conf={'triggered_by': 'multi_trigger'}
        )
        trigger_tasks.append(trigger)
    
    # Execute all triggers in parallel
    start >> trigger_tasks >> end
```

---

## Modern Alternative: TaskFlow API (Airflow 2.4+)

### Using TriggerDagRunOperator with TaskFlow

```python
from airflow.decorators import dag, task
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime

@dag(
    dag_id='taskflow_trigger',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def taskflow_trigger_example():
    
    @task
    def prepare_data():
        return {
            'message': 'Data prepared',
            'timestamp': datetime.now().isoformat()
        }
    
    # Prepare configuration
    config = prepare_data()
    
    # Trigger another DAG
    trigger = TriggerDagRunOperator(
        task_id='trigger_dag',
        trigger_dag_id='triggered_dag',
        conf=config
    )
    
    @task
    def log_trigger():
        print("DAG triggered successfully")
    
    # Set dependencies
    config >> trigger >> log_trigger()

dag_instance = taskflow_trigger_example()
```

---

## Parameters Reference

| Parameter | Description | Default |
|-----------|-------------|---------|
| `trigger_dag_id` | ID of the DAG to trigger (required) | - |
| `conf` | Configuration dictionary to pass to triggered DAG | `None` |
| `execution_date` | Execution date for triggered DAG run | Current execution date |
| `wait_for_completion` | Wait for triggered DAG to complete | `False` |
| `poke_interval` | Seconds between status checks (if waiting) | `60` |
| `allowed_states` | States considered successful | `['success']` |
| `failed_states` | States considered failed | `['failed']` |
| `reset_dag_run` | Clear existing DAG run before triggering | `False` |

---

## Accessing Passed Configuration

In the triggered DAG, access the configuration data:

```python
def my_task(**kwargs):
    # Method 1: From dag_run.conf
    dag_run = kwargs.get('dag_run')
    if dag_run and dag_run.conf:
        message = dag_run.conf.get('message')
        print(f"Received: {message}")
    
    # Method 2: From context
    conf = kwargs.get('dag_run').conf
    print(f"Full config: {conf}")
```

---

## Best Practices

1. **Set schedule_interval=None**: For triggered DAGs, set `schedule_interval=None` to prevent automatic scheduling

2. **Use Meaningful Configuration**: Pass relevant context and data through the `conf` parameter

3. **Handle Missing Configuration**: Always check if configuration exists before accessing it

4. **Consider wait_for_completion**: Use `wait_for_completion=True` when downstream tasks depend on the triggered DAG's results

5. **Monitor Triggered DAGs**: Set up proper logging and monitoring for triggered DAGs

6. **Avoid Circular Triggers**: Don't create circular dependencies between DAGs

7. **Use Tags**: Tag related DAGs for easier management and monitoring

8. **Error Handling**: Implement proper error handling in both triggering and triggered DAGs

---

## Common Use Cases

1. **ETL Pipeline Orchestration**: Trigger data processing DAGs after data extraction completes

2. **Multi-Stage Workflows**: Break complex workflows into smaller, manageable DAGs

3. **Environment-Specific Processing**: Trigger different DAGs based on environment or conditions

4. **Batch Processing**: Trigger processing DAGs when data batches are ready

5. **Notification Workflows**: Trigger notification DAGs after critical tasks complete

---

## Troubleshooting

### DAG Not Triggering

- Verify `trigger_dag_id` matches the target DAG's `dag_id`
- Ensure target DAG is not paused in the UI
- Check Airflow logs for error messages

### Configuration Not Received

- Verify `conf` parameter is properly formatted as a dictionary
- Check that triggered DAG is accessing `dag_run.conf` correctly
- Ensure `provide_context=True` in PythonOperator tasks

### Performance Issues

- Avoid triggering too many DAGs simultaneously
- Consider using `wait_for_completion=False` for independent workflows
- Monitor scheduler performance and resource usage

---

## Migration from Legacy Syntax

### Before (Airflow 1.x)

```python
from airflow.operators.dagrun_operator import TriggerDagRunOperator

def conditionally_trigger(context, dag_run_obj):
    dag_run_obj.payload = {'message': 'data'}
    return dag_run_obj

trigger = TriggerDagRunOperator(
    task_id='trigger',
    trigger_dag_id='target_dag',
    python_callable=conditionally_trigger,
    params={'message': 'Hello'}
)
```

### After (Airflow 2.x)

```python
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

trigger = TriggerDagRunOperator(
    task_id='trigger',
    trigger_dag_id='target_dag',
    conf={'message': 'Hello'}
)
```

---

## Additional Resources

- [TriggerDagRunOperator Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/trigger_dagrun.html)
- [DAG Dependencies](https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html#dag-dependencies)
- [Cross-DAG Dependencies](https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/external_task_sensor.html)
