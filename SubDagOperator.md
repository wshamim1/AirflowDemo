# SubDagOperator (Deprecated)

> **⚠️ DEPRECATION NOTICE**: SubDagOperator is deprecated as of Airflow 2.0 and will be removed in a future version. Use **TaskGroup** instead for better performance and simpler code.

## Overview

SubDagOperator was used to create nested DAGs within a parent DAG. However, it had several limitations:
- Performance issues with the scheduler
- Complex debugging
- Resource management challenges
- Confusing UI representation

## Legacy Example (Not Recommended)

### Step 1: Create Parent DAG

```python
from airflow import DAG
from airflow.operators.subdag import SubDagOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
}

parent_dag = DAG(
    dag_id='parent_dag',
    default_args=args,
    schedule_interval='@hourly',
    dagrun_timeout=timedelta(minutes=60)
)
```

### Step 2: Create SubDAG Function

```python
from airflow.operators.dummy import DummyOperator

def create_subdag(parent_dag_id, child_dag_id, args):
    """
    Generate a subdag.
    """
    subdag = DAG(
        dag_id=f'{parent_dag_id}.{child_dag_id}',
        default_args=args,
        schedule_interval='@hourly',
    )
    
    with subdag:
        start = DummyOperator(task_id='start')
        end = DummyOperator(task_id='end')
        
        # Create tasks within subdag
        for i in range(5):
            task = DummyOperator(task_id=f'task_{i}')
            start >> task >> end
    
    return subdag
```

### Step 3: Use SubDagOperator in Parent DAG

```python
with parent_dag:
    start = DummyOperator(task_id='start')
    
    subdag_task = SubDagOperator(
        task_id='subdag_operator',
        subdag=create_subdag('parent_dag', 'subdag_operator', args),
        default_args=args,
    )
    
    end = DummyOperator(task_id='end')
    
    start >> subdag_task >> end
```

![SubDAG Example](images/subdag.png)

---

## Modern Alternative: TaskGroup (Recommended)

TaskGroup provides the same organizational benefits without the performance overhead.

### Basic TaskGroup Example

```python
from airflow import DAG
from airflow.utils.task_group import TaskGroup
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
from datetime import datetime

def process_data(task_id, **kwargs):
    print(f"Processing in {task_id}")

dag = DAG(
    dag_id='taskgroup_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['example', 'taskgroup']
)

with dag:
    start = DummyOperator(task_id='start')
    end = DummyOperator(task_id='end')
    
    # Create a TaskGroup (replaces SubDAG)
    with TaskGroup(group_id='processing_group') as processing_group:
        group_start = DummyOperator(task_id='group_start')
        group_end = DummyOperator(task_id='group_end')
        
        # Create tasks within the group
        for i in range(5):
            task = PythonOperator(
                task_id=f'task_{i}',
                python_callable=process_data,
                op_kwargs={'task_id': f'task_{i}'}
            )
            group_start >> task >> group_end
    
    # Set dependencies
    start >> processing_group >> end
```

### Nested TaskGroups

```python
from airflow import DAG
from airflow.utils.task_group import TaskGroup
from airflow.operators.dummy import DummyOperator
from datetime import datetime

dag = DAG(
    dag_id='nested_taskgroups',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

with dag:
    start = DummyOperator(task_id='start')
    
    # Parent TaskGroup
    with TaskGroup(group_id='parent_group') as parent_group:
        parent_start = DummyOperator(task_id='parent_start')
        
        # Nested TaskGroup 1
        with TaskGroup(group_id='child_group_1') as child_group_1:
            for i in range(3):
                DummyOperator(task_id=f'child1_task_{i}')
        
        # Nested TaskGroup 2
        with TaskGroup(group_id='child_group_2') as child_group_2:
            for i in range(3):
                DummyOperator(task_id=f'child2_task_{i}')
        
        parent_end = DummyOperator(task_id='parent_end')
        
        parent_start >> [child_group_1, child_group_2] >> parent_end
    
    end = DummyOperator(task_id='end')
    
    start >> parent_group >> end
```

### Dynamic TaskGroups

```python
from airflow import DAG
from airflow.utils.task_group import TaskGroup
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime

def process_section(section_id, item_id, **kwargs):
    print(f"Processing section {section_id}, item {item_id}")

dag = DAG(
    dag_id='dynamic_taskgroups',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

sections = ['section_a', 'section_b', 'section_c']

with dag:
    start = DummyOperator(task_id='start')
    end = DummyOperator(task_id='end')
    
    # Create multiple TaskGroups dynamically
    for section in sections:
        with TaskGroup(group_id=section) as section_group:
            section_start = DummyOperator(task_id='start')
            section_end = DummyOperator(task_id='end')
            
            # Create tasks within each group
            for i in range(3):
                task = PythonOperator(
                    task_id=f'process_item_{i}',
                    python_callable=process_section,
                    op_kwargs={'section_id': section, 'item_id': i}
                )
                section_start >> task >> section_end
        
        start >> section_group >> end
```

### TaskGroup with TaskFlow API

```python
from airflow.decorators import dag, task, task_group
from datetime import datetime

@dag(
    dag_id='taskgroup_with_taskflow',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def taskgroup_taskflow_example():
    
    @task
    def start_task():
        print("Starting workflow")
        return "started"
    
    @task_group(group_id='processing_group')
    def processing_tasks():
        
        @task
        def extract():
            print("Extracting data")
            return "extracted"
        
        @task
        def transform(data):
            print(f"Transforming {data}")
            return "transformed"
        
        @task
        def load(data):
            print(f"Loading {data}")
            return "loaded"
        
        # Define task flow within group
        data = extract()
        transformed = transform(data)
        load(transformed)
    
    @task
    def end_task():
        print("Workflow complete")
        return "complete"
    
    # Define overall flow
    start = start_task()
    process = processing_tasks()
    end = end_task()
    
    start >> process >> end

# Instantiate the DAG
dag_instance = taskgroup_taskflow_example()
```

---

## Comparison: SubDAG vs TaskGroup

| Feature | SubDAG (Deprecated) | TaskGroup (Recommended) |
|---------|---------------------|-------------------------|
| Performance | Poor (separate DAG run) | Excellent (same DAG run) |
| UI Representation | Separate DAG view | Collapsible group in same view |
| Debugging | Complex | Simple |
| Resource Management | Separate executor slots | Shared with parent DAG |
| Code Complexity | High | Low |
| Airflow Version | All (deprecated in 2.0) | 2.0+ |

---

## Migration Guide: SubDAG to TaskGroup

### Before (SubDAG)

```python
def create_subdag(parent_id, child_id, args):
    subdag = DAG(f'{parent_id}.{child_id}', default_args=args)
    # tasks...
    return subdag

subdag_op = SubDagOperator(
    task_id='subdag',
    subdag=create_subdag('parent', 'subdag', args)
)
```

### After (TaskGroup)

```python
with TaskGroup(group_id='taskgroup') as taskgroup:
    # tasks...
    pass
```

---

## Best Practices for TaskGroups

1. **Naming**: Use descriptive group_id names that reflect the group's purpose

2. **Organization**: Group related tasks together logically

3. **Nesting**: Limit nesting depth to 2-3 levels for readability

4. **UI Clarity**: TaskGroups appear as collapsible sections in the Airflow UI

5. **Dependencies**: Set dependencies at the group level when possible

6. **Documentation**: Add tooltips or descriptions to TaskGroups:
   ```python
   with TaskGroup(
       group_id='processing',
       tooltip='Data processing tasks'
   ) as processing:
       # tasks...
   ```

---

## Additional Resources

- [TaskGroup Documentation](https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html#taskgroups)
- [SubDAG Deprecation Notice](https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html#subdags)
- [Migration Guide](https://airflow.apache.org/docs/apache-airflow/stable/howto/operator/subdag.html)
