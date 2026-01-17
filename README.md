# Apache Airflow Documentation and Examples

A comprehensive collection of Apache Airflow documentation, examples, and best practices for building robust data pipelines.

## 📚 Documentation Overview

This repository contains detailed guides and examples for various Airflow concepts:

### Core Concepts

1. **[Operators](Operator.md)** - Building blocks of Airflow DAGs
   - PythonOperator, BashOperator, DummyOperator
   - TaskFlow API with @task decorator
   - Modern Airflow 2.x syntax
   - Best practices and examples

2. **[Task Dependencies & Flow Patterns](Tasks%20flow.md)** - Defining workflow structure
   - Sequential, parallel, and branching patterns
   - Dependency operators (>>, <<, chain, cross_downstream)
   - TaskFlow API examples
   - Complete ETL pipeline examples

3. **[Dynamic Tasks](Dynamic%20Tasks.md)** - Creating tasks programmatically
   - Dynamic task generation patterns
   - TaskFlow API for dynamic workflows
   - Task Groups for organization
   - Configuration-driven task creation

### Advanced Operators

4. **[BranchPythonOperator](BranchPythonOperator.md)** - Conditional workflow execution
   - Branching logic implementation
   - Multiple branch patterns
   - @task.branch decorator (Airflow 2.0+)
   - Use cases and examples

5. **[TriggerDagRunOperator](TriggerDagRunOperator.md)** - DAG orchestration
   - Triggering external DAGs
   - Passing configuration between DAGs
   - Wait for completion patterns
   - Modern Airflow 2.x syntax

6. **[SubDagOperator](SubDagOperator.md)** - Nested workflows (Deprecated)
   - Legacy SubDAG patterns
   - **⚠️ Deprecation notice**
   - Migration to TaskGroup (recommended)
   - Modern alternatives

### Data Exchange & Communication

7. **[XCom](XCom.md)** - Cross-task communication
   - Pushing and pulling data between tasks
   - TaskFlow API automatic XCom handling
   - Best practices for data sharing
   - Size limitations and workarounds

8. **[Sensors](Sensors.md)** - Waiting for conditions
   - FileSensor, S3KeySensor, SqlSensor
   - ExternalTaskSensor for DAG coordination
   - Custom sensor creation
   - Poke vs Reschedule modes

### Integration & Configuration

9. **[Hooks](Hooks.md)** - External system integration
   - PostgresHook, MySqlHook, S3Hook
   - HttpHook for API integration
   - Custom hook creation
   - Connection management

10. **[Variables and Connections](Variables-and-Connections.md)** - Configuration management
    - Storing and retrieving variables
    - Managing external connections
    - Security best practices
    - Secrets backend integration

## 🚀 Quick Start

### Basic DAG Example

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='hello_world',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def hello_world_dag():
    
    @task
    def hello():
        print("Hello, Airflow!")
        return "Hello"
    
    @task
    def world(message):
        print(f"{message}, World!")
    
    message = hello()
    world(message)

dag_instance = hello_world_dag()
```

### ETL Pipeline Example

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='simple_etl',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def simple_etl():
    
    @task
    def extract():
        # Extract data from source
        return {'records': 100, 'source': 'database'}
    
    @task
    def transform(data):
        # Transform data
        data['transformed'] = True
        return data
    
    @task
    def load(data):
        # Load data to destination
        print(f"Loading {data['records']} records")
        return "Success"
    
    data = extract()
    transformed = transform(data)
    load(transformed)

dag_instance = simple_etl()
```

## 📖 Learning Path

### Beginner
1. Start with [Operators](Operator.md) to understand basic building blocks
2. Learn [Task Dependencies](Tasks%20flow.md) for workflow structure
3. Explore [Variables and Connections](Variables-and-Connections.md) for configuration

### Intermediate
4. Master [XCom](XCom.md) for data sharing between tasks
5. Implement [Sensors](Sensors.md) for external dependencies
6. Use [Dynamic Tasks](Dynamic%20Tasks.md) for flexible workflows

### Advanced
7. Create [Custom Hooks](Hooks.md) for external integrations
8. Implement [Branching Logic](BranchPythonOperator.md) for conditional workflows
9. Orchestrate multiple DAGs with [TriggerDagRunOperator](TriggerDagRunOperator.md)

## 🎯 Best Practices

### 1. Use TaskFlow API (Airflow 2.0+)
```python
# ✅ Modern approach
@task
def my_task():
    return "result"

# ❌ Legacy approach
def my_function():
    return "result"

task = PythonOperator(
    task_id='my_task',
    python_callable=my_function
)
```

### 2. Leverage TaskGroups Instead of SubDAGs
```python
# ✅ Recommended
from airflow.utils.task_group import TaskGroup

with TaskGroup(group_id='processing') as group:
    task1 = my_task_1()
    task2 = my_task_2()

# ❌ Deprecated
from airflow.operators.subdag import SubDagOperator
```

### 3. Use Appropriate Sensor Modes
```python
# ✅ For long waits
sensor = FileSensor(
    task_id='wait',
    filepath='/path/to/file',
    mode='reschedule',  # Frees worker slot
    poke_interval=300
)

# ✅ For short waits
sensor = FileSensor(
    task_id='wait',
    filepath='/path/to/file',
    mode='poke',  # Keeps worker slot
    poke_interval=10
)
```

### 4. Secure Sensitive Data
```python
# ✅ Use Variables with secure naming
Variable.set("api_key_secret", "sensitive-value")  # Masked in UI

# ✅ Use Connections for credentials
hook = PostgresHook(postgres_conn_id='postgres_default')

# ❌ Hardcode credentials
password = "hardcoded_password"  # Never do this!
```

### 5. Handle Errors Gracefully
```python
@task
def robust_task():
    try:
        # Your logic
        result = process_data()
        return result
    except Exception as e:
        print(f"Error: {e}")
        # Handle error appropriately
        raise
```

## 🔧 Common Patterns

### Pattern 1: Fan-Out / Fan-In
```python
@dag(dag_id='fan_out_in', start_date=datetime(2024, 1, 1))
def fan_pattern():
    @task
    def start():
        return "Starting"
    
    @task
    def process(item_id):
        return f"Processed {item_id}"
    
    @task
    def aggregate(results):
        return f"Aggregated {len(results)} results"
    
    start_task = start()
    
    # Fan-out: Process multiple items in parallel
    results = [process(i) for i in range(5)]
    
    # Fan-in: Aggregate results
    start_task >> results >> aggregate(results)
```

### Pattern 2: Conditional Execution
```python
@dag(dag_id='conditional', start_date=datetime(2024, 1, 1))
def conditional_pattern():
    @task.branch
    def check_condition():
        if condition_met():
            return 'process_data'
        return 'skip_processing'
    
    @task
    def process_data():
        return "Processing"
    
    @task
    def skip_processing():
        return "Skipped"
    
    check_condition() >> [process_data(), skip_processing()]
```

### Pattern 3: Data Pipeline with Error Handling
```python
@dag(dag_id='robust_pipeline', start_date=datetime(2024, 1, 1))
def robust_pipeline():
    @task
    def extract():
        try:
            return extract_data()
        except Exception as e:
            send_alert(f"Extract failed: {e}")
            raise
    
    @task
    def transform(data):
        return transform_data(data)
    
    @task
    def load(data):
        return load_data(data)
    
    @task
    def notify_success():
        send_notification("Pipeline completed!")
    
    data = extract()
    transformed = transform(data)
    loaded = load(transformed)
    loaded >> notify_success()
```

## 🛠️ Troubleshooting

### Common Issues

1. **DAG not appearing in UI**
   - Check for syntax errors
   - Verify DAG file is in dags folder
   - Check scheduler logs

2. **Tasks not running**
   - Verify DAG is unpaused
   - Check task dependencies
   - Review task logs

3. **XCom size limit exceeded**
   - Use external storage (S3, database)
   - Pass references instead of large data
   - Configure custom XCom backend

4. **Sensor timing out**
   - Increase timeout parameter
   - Adjust poke_interval
   - Use reschedule mode for long waits

## 📊 Project Structure

```
AirflowDemo/
├── README.md                          # This file
├── Operator.md                        # Operators guide
├── Tasks flow.md                      # Task dependencies
├── Dynamic Tasks.md                   # Dynamic task generation
├── BranchPythonOperator.md           # Conditional workflows
├── TriggerDagRunOperator.md          # DAG orchestration
├── SubDagOperator.md                 # SubDAGs (deprecated)
├── XCom.md                           # Cross-task communication
├── Sensors.md                        # Waiting for conditions
├── Hooks.md                          # External integrations
├── Variables-and-Connections.md      # Configuration management
├── examples/                         # Example DAG files
│   ├── sampleDag1.py                # Basic DAG example
│   └── CreateDynamicDags.py         # Dynamic DAG creation example
└── images/                           # Documentation images
    ├── BranchPythonOperator.png
    ├── dynamic_parallel.png
    ├── parallel_seq.png
    ├── sequential.png
    ├── subdag.png
    └── triggerDagRun.png
```

## 🔗 Additional Resources

### Official Documentation
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Airflow GitHub Repository](https://github.com/apache/airflow)
- [Airflow Provider Packages](https://airflow.apache.org/docs/apache-airflow-providers/)

### Community
- [Airflow Slack Community](https://apache-airflow-slack.herokuapp.com/)
- [Stack Overflow - Airflow Tag](https://stackoverflow.com/questions/tagged/airflow)
- [Airflow Summit](https://airflowsummit.org/)

### Learning Resources
- [Astronomer Guides](https://docs.astronomer.io/learn/)
- [Airflow Tutorial](https://airflow.apache.org/docs/apache-airflow/stable/tutorial.html)
- [TaskFlow API Tutorial](https://airflow.apache.org/docs/apache-airflow/stable/tutorial_taskflow_api.html)

## 📝 Version Information

- **Airflow Version**: 2.x (examples use modern syntax)
- **Python Version**: 3.8+
- **Last Updated**: January 2024

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Examples use modern Airflow 2.x syntax
- Code is well-documented
- Best practices are followed
- Examples are tested

## 📄 License

This documentation is provided as-is for educational purposes.

## 🎓 About

This repository serves as a comprehensive guide for Apache Airflow, covering everything from basic concepts to advanced patterns. Each document includes:
- Detailed explanations
- Working code examples
- Best practices
- Common pitfalls to avoid
- Troubleshooting tips

Happy DAG building! 🚀