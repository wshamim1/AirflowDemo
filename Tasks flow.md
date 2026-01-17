# Task Dependencies and Flow Patterns in Airflow

This guide demonstrates various patterns for defining task dependencies and workflow structures in Apache Airflow.

## Overview

Task dependencies define the order in which tasks execute. Airflow provides flexible syntax for creating simple sequential flows, parallel execution, and complex branching patterns.

## Basic Setup

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
    dag_id='task_flow_patterns',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['example', 'patterns']
)

# Sample Python functions
def extract_data(**kwargs):
    print('Extracting data...')
    return 'data_extracted'

def transform_data(**kwargs):
    print('Transforming data...')
    return 'data_transformed'

# Define tasks
start = DummyOperator(task_id='start', dag=dag)
task_one = PythonOperator(task_id='one', python_callable=extract_data, dag=dag)
task_two = PythonOperator(task_id='two', python_callable=transform_data, dag=dag)
task_three = DummyOperator(task_id='three', dag=dag)
task_four = DummyOperator(task_id='four', dag=dag)
task_five = DummyOperator(task_id='five', dag=dag)
task_six = DummyOperator(task_id='six', dag=dag)
end = DummyOperator(task_id='end', dag=dag)
```

---

## Pattern 1: Sequential Tasks

All tasks execute one after another in a linear sequence.

### Syntax

```python
start >> task_one >> task_two >> task_three >> task_four >> task_five >> task_six >> end
```

### Alternative Syntax

```python
# Using set_downstream
start.set_downstream(task_one)
task_one.set_downstream(task_two)
# ... and so on

# Using set_upstream
task_two.set_upstream(task_one)
task_three.set_upstream(task_two)
# ... and so on
```

### Visual Representation

![Sequential Tasks](images/sequential.png)

**Use Case**: ETL pipelines where each step depends on the previous one completing successfully.

---

## Pattern 2: Parallel Tasks with Sequential Bookends

Multiple tasks execute in parallel, with sequential tasks before and after.

### Syntax

```python
start >> [task_two, task_three, task_four] >> task_five >> task_six >> end
```

### Explanation

- `start` executes first
- `task_two`, `task_three`, and `task_four` execute in parallel
- Once all three complete, `task_five` executes
- Then `task_six` and finally `end`

### Visual Representation

![Parallel with Sequential](images/parallel_seq.png)

**Use Case**: Processing multiple data sources simultaneously, then aggregating results.

---

## Pattern 3: Multiple Parallel Branches

Two independent sequential branches that converge.

### Syntax

```python
# Branch 1
start >> task_two >> task_three

# Branch 2
start >> task_four >> task_five

# Convergence
[task_three, task_five] >> task_six >> end
```

### Alternative Syntax

```python
# More explicit
start >> task_two
start >> task_four

task_two >> task_three
task_four >> task_five

task_three >> task_six
task_five >> task_six

task_six >> end
```

### Visual Representation

![Parallel Sequential Branches](images/parallel_seq_1].png)

**Use Case**: Processing different data pipelines independently, then combining results.

---

## Pattern 4: Complex Branching and Merging

Multiple branches with different convergence points.

### Syntax

```python
# Initial split
start >> [task_two, task_three]

# Branch from task_three
task_three >> [task_four, task_five]

# Branch from task_two
task_two >> task_six

# Convergence points
task_six >> end
[task_four, task_five] >> end
```

### Visual Representation

![Complex Branching](images/img1.png)

**Use Case**: Complex workflows with conditional processing and multiple aggregation points.

---

## Modern Syntax with TaskFlow API (Airflow 2.0+)

### Sequential Pattern

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='taskflow_sequential',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def sequential_taskflow():
    
    @task
    def extract():
        print("Extracting data")
        return {'data': 'extracted'}
    
    @task
    def transform(data):
        print(f"Transforming {data}")
        return {'data': 'transformed'}
    
    @task
    def load(data):
        print(f"Loading {data}")
        return "Complete"
    
    # Define flow
    data = extract()
    transformed = transform(data)
    load(transformed)

dag_instance = sequential_taskflow()
```

### Parallel Pattern

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='taskflow_parallel',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def parallel_taskflow():
    
    @task
    def start_task():
        return "Starting"
    
    @task
    def process_a():
        print("Processing A")
        return "A_complete"
    
    @task
    def process_b():
        print("Processing B")
        return "B_complete"
    
    @task
    def process_c():
        print("Processing C")
        return "C_complete"
    
    @task
    def aggregate(results):
        print(f"Aggregating: {results}")
        return "All complete"
    
    # Define parallel flow
    start = start_task()
    
    # These run in parallel
    result_a = process_a()
    result_b = process_b()
    result_c = process_c()
    
    # Wait for all to complete
    start >> [result_a, result_b, result_c]
    aggregate([result_a, result_b, result_c])

dag_instance = parallel_taskflow()
```

---

## Dependency Operators

### Bitshift Operators (Recommended)

```python
# Downstream
task_a >> task_b  # task_b runs after task_a

# Upstream
task_b << task_a  # task_b runs after task_a

# Multiple dependencies
task_a >> [task_b, task_c]  # task_b and task_c run after task_a
[task_a, task_b] >> task_c  # task_c runs after both task_a and task_b
```

### Method Calls

```python
# set_downstream
task_a.set_downstream(task_b)
task_a.set_downstream([task_b, task_c])

# set_upstream
task_b.set_upstream(task_a)
task_c.set_upstream([task_a, task_b])
```

### Chain Function

```python
from airflow.models.baseoperator import chain

# Linear chain
chain(task_a, task_b, task_c, task_d)

# Equivalent to: task_a >> task_b >> task_c >> task_d

# Complex chains
chain(
    task_a,
    [task_b, task_c],  # Parallel
    task_d
)
```

### Cross Dependencies

```python
from airflow.models.baseoperator import cross_downstream

# Create all-to-all dependencies
cross_downstream([task_a, task_b], [task_c, task_d])

# Equivalent to:
# task_a >> task_c
# task_a >> task_d
# task_b >> task_c
# task_b >> task_d
```

---

## Advanced Patterns

### Fan-Out / Fan-In

```python
# Fan-out: One task triggers multiple parallel tasks
start >> [task_1, task_2, task_3, task_4, task_5]

# Fan-in: Multiple tasks converge to one
[task_1, task_2, task_3, task_4, task_5] >> end
```

### Diamond Pattern

```python
start >> [task_a, task_b]
task_a >> task_c
task_b >> task_c
task_c >> end
```

### Conditional Branching

```python
from airflow.operators.python import BranchPythonOperator

def choose_branch(**kwargs):
    # Logic to choose branch
    return 'task_a' if condition else 'task_b'

branch = BranchPythonOperator(
    task_id='branch',
    python_callable=choose_branch,
    dag=dag
)

start >> branch >> [task_a, task_b] >> end
```

---

## Best Practices

1. **Keep It Simple**: Start with simple patterns and add complexity only when needed

2. **Use Bitshift Operators**: The `>>` and `<<` operators are more readable than method calls

3. **Group Related Tasks**: Use TaskGroups to organize related tasks

4. **Avoid Circular Dependencies**: Airflow will reject DAGs with circular dependencies

5. **Document Complex Flows**: Add comments explaining non-obvious dependency patterns

6. **Test Dependencies**: Use `airflow dags test` to verify your dependency structure

7. **Visualize**: Always check the Graph view in the Airflow UI to verify your flow

---

## Common Mistakes to Avoid

### ❌ Circular Dependencies

```python
# This will fail!
task_a >> task_b >> task_c >> task_a
```

### ❌ Duplicate Dependencies

```python
# Redundant - task_c already depends on task_a through task_b
task_a >> task_b >> task_c
task_a >> task_c  # Unnecessary
```

### ✅ Correct Approach

```python
# Clear and efficient
task_a >> task_b >> task_c
```

---

## Debugging Tips

1. **Check DAG Structure**: Use `airflow dags show <dag_id>` to visualize dependencies

2. **Validate DAG**: Run `airflow dags test <dag_id> <execution_date>` to test without scheduling

3. **Check Logs**: Review task logs for dependency-related errors

4. **Use Graph View**: The Airflow UI's Graph view is invaluable for understanding flow

---

## Complete Example: ETL Pipeline

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime

def extract_from_source_a(**kwargs):
    print("Extracting from source A")
    return "data_a"

def extract_from_source_b(**kwargs):
    print("Extracting from source B")
    return "data_b"

def transform_data(**kwargs):
    print("Transforming data")
    return "transformed_data"

def load_to_warehouse(**kwargs):
    print("Loading to warehouse")
    return "loaded"

def send_notification(**kwargs):
    print("Sending notification")

dag = DAG(
    dag_id='etl_pipeline_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

with dag:
    start = DummyOperator(task_id='start')
    
    # Parallel extraction
    extract_a = PythonOperator(task_id='extract_a', python_callable=extract_from_source_a)
    extract_b = PythonOperator(task_id='extract_b', python_callable=extract_from_source_b)
    
    # Transform after both extractions complete
    transform = PythonOperator(task_id='transform', python_callable=transform_data)
    
    # Load transformed data
    load = PythonOperator(task_id='load', python_callable=load_to_warehouse)
    
    # Notify after load
    notify = PythonOperator(task_id='notify', python_callable=send_notification)
    
    end = DummyOperator(task_id='end')
    
    # Define flow
    start >> [extract_a, extract_b] >> transform >> load >> notify >> end
```

---

## Additional Resources

- [Airflow Task Dependencies Documentation](https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html#task-dependencies)
- [TaskFlow API Guide](https://airflow.apache.org/docs/apache-airflow/stable/tutorial_taskflow_api.html)
- [Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
