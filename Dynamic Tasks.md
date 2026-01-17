# Dynamic Tasks in Airflow

Dynamic task generation allows you to create tasks programmatically at DAG parse time, enabling flexible and scalable workflows.

## Overview

Dynamic tasks are useful when:
- The number of tasks depends on external data or configuration
- You need to process multiple similar items in parallel
- Task structure needs to be flexible and data-driven

## Basic Example: Dynamic Parallel Tasks

### Simple Grid Pattern

```python
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
}

dag = DAG(
    dag_id='dynamic_tasks_example',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['example', 'dynamic']
)

with dag:
    start = DummyOperator(task_id='start')
    end = DummyOperator(task_id='end')
    
    # Create a 3x3 grid of parallel tasks
    for x in range(3):
        for y in range(3):
            task = DummyOperator(task_id=f'task_{x}_{y}')
            start >> task >> end
```

![Dynamic Parallel Tasks](images/dynamic_parallel.png)

## Advanced Examples

### 1. Dynamic Tasks from List

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime

def process_item(item_name, **kwargs):
    print(f"Processing {item_name}")
    # Your processing logic here

# List of items to process (could come from a config file or database)
items_to_process = ['item_a', 'item_b', 'item_c', 'item_d', 'item_e']

dag = DAG(
    dag_id='dynamic_from_list',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

with dag:
    start = DummyOperator(task_id='start')
    end = DummyOperator(task_id='end')
    
    for item in items_to_process:
        task = PythonOperator(
            task_id=f'process_{item}',
            python_callable=process_item,
            op_kwargs={'item_name': item}
        )
        start >> task >> end
```

### 2. Dynamic Tasks with TaskFlow API (Airflow 2.0+)

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='dynamic_taskflow',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def dynamic_taskflow_example():
    
    @task
    def start_task():
        return "Starting dynamic workflow"
    
    @task
    def process_item(item_id: int):
        print(f"Processing item {item_id}")
        return f"Processed item {item_id}"
    
    @task
    def end_task(results):
        print(f"All items processed: {results}")
        return "Complete"
    
    # Generate dynamic tasks
    start = start_task()
    
    # Create multiple parallel tasks
    results = [process_item(i) for i in range(5)]
    
    # Collect results
    end = end_task(results)
    
    start >> results >> end

# Instantiate the DAG
dag_instance = dynamic_taskflow_example()
```

### 3. Dynamic Task Groups (Airflow 2.0+)

```python
from airflow import DAG
from airflow.utils.task_group import TaskGroup
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
from datetime import datetime

def process_data(group_id, task_id, **kwargs):
    print(f"Processing {group_id} - {task_id}")

dag = DAG(
    dag_id='dynamic_task_groups',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

with dag:
    start = DummyOperator(task_id='start')
    end = DummyOperator(task_id='end')
    
    # Create multiple task groups dynamically
    for group_num in range(3):
        with TaskGroup(group_id=f'group_{group_num}') as tg:
            group_start = DummyOperator(task_id='group_start')
            group_end = DummyOperator(task_id='group_end')
            
            # Create tasks within each group
            for task_num in range(3):
                task = PythonOperator(
                    task_id=f'task_{task_num}',
                    python_callable=process_data,
                    op_kwargs={
                        'group_id': f'group_{group_num}',
                        'task_id': f'task_{task_num}'
                    }
                )
                group_start >> task >> group_end
        
        start >> tg >> end
```

### 4. Dynamic Tasks from Configuration

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime
import json

# Configuration could come from a file, database, or Variable
config = {
    'databases': ['db1', 'db2', 'db3'],
    'tables_per_db': ['table_a', 'table_b']
}

def extract_data(database, table, **kwargs):
    print(f"Extracting from {database}.{table}")

dag = DAG(
    dag_id='dynamic_from_config',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

with dag:
    start = DummyOperator(task_id='start')
    end = DummyOperator(task_id='end')
    
    for db in config['databases']:
        for table in config['tables_per_db']:
            task = PythonOperator(
                task_id=f'extract_{db}_{table}',
                python_callable=extract_data,
                op_kwargs={'database': db, 'table': table}
            )
            start >> task >> end
```

## Best Practices

1. **Limit Task Count**: Too many tasks can slow down the scheduler. Consider batching if you need thousands of tasks.

2. **Use Task Groups**: For better organization and UI readability, group related dynamic tasks.

3. **Naming Convention**: Use clear, consistent naming patterns for dynamic tasks (e.g., `process_{item_id}`).

4. **Configuration Management**: Store dynamic task configurations in Airflow Variables or external config files.

5. **Performance**: Dynamic task generation happens at DAG parse time, so keep the generation logic efficient.

## Common Patterns

- **Fan-out/Fan-in**: Start → Multiple parallel tasks → End
- **Grid Processing**: Process data in a matrix pattern
- **Hierarchical**: Create nested groups of dynamic tasks
- **Conditional**: Generate tasks based on runtime conditions

## Troubleshooting

- **DAG not appearing**: Check for syntax errors in dynamic task generation
- **Too many tasks**: Consider using mapped tasks (Airflow 2.3+) or batching
- **Slow parsing**: Optimize the logic that generates tasks
