# Airflow Hooks

Hooks are interfaces to external platforms and databases. They provide a consistent way to interact with external systems and handle connections.

## Overview

Hooks:
- Encapsulate connection logic
- Provide reusable interfaces to external systems
- Handle authentication and connection management
- Can be used in Operators, Sensors, and custom code

## Common Hooks

### 1. PostgresHook

Interact with PostgreSQL databases.

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime

def query_postgres(**kwargs):
    """Query PostgreSQL using Hook"""
    # Initialize hook with connection ID
    hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Execute query and fetch results
    sql = "SELECT * FROM users WHERE created_date = %s"
    results = hook.get_records(sql, parameters=[kwargs['ds']])
    
    print(f"Found {len(results)} records")
    for row in results:
        print(row)
    
    return len(results)

dag = DAG(
    dag_id='postgres_hook_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

query_task = PythonOperator(
    task_id='query_postgres',
    python_callable=query_postgres,
    dag=dag
)
```

### 2. MySqlHook

Interact with MySQL databases.

```python
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='mysql_hook_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def mysql_example():
    
    @task
    def extract_from_mysql():
        """Extract data from MySQL"""
        hook = MySqlHook(mysql_conn_id='mysql_default')
        
        # Get connection
        conn = hook.get_conn()
        cursor = conn.cursor()
        
        # Execute query
        cursor.execute("SELECT id, name, value FROM products")
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [{'id': r[0], 'name': r[1], 'value': r[2]} for r in results]
    
    @task
    def process_data(data):
        print(f"Processing {len(data)} records")
        return data
    
    data = extract_from_mysql()
    process_data(data)

dag_instance = mysql_example()
```

### 3. S3Hook

Interact with Amazon S3.

```python
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.decorators import dag, task
from datetime import datetime
import json

@dag(
    dag_id='s3_hook_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def s3_example():
    
    @task
    def upload_to_s3():
        """Upload data to S3"""
        hook = S3Hook(aws_conn_id='aws_default')
        
        # Prepare data
        data = {'date': '2024-01-01', 'records': 100}
        
        # Upload to S3
        hook.load_string(
            string_data=json.dumps(data),
            key='data/output.json',
            bucket_name='my-bucket',
            replace=True
        )
        
        print("Data uploaded to S3")
        return 's3://my-bucket/data/output.json'
    
    @task
    def download_from_s3(s3_path):
        """Download data from S3"""
        hook = S3Hook(aws_conn_id='aws_default')
        
        # Download file
        content = hook.read_key(
            key='data/output.json',
            bucket_name='my-bucket'
        )
        
        data = json.loads(content)
        print(f"Downloaded data: {data}")
        return data
    
    @task
    def list_s3_files():
        """List files in S3 bucket"""
        hook = S3Hook(aws_conn_id='aws_default')
        
        # List files with prefix
        keys = hook.list_keys(
            bucket_name='my-bucket',
            prefix='data/',
            delimiter='/'
        )
        
        print(f"Found {len(keys)} files")
        return keys
    
    path = upload_to_s3()
    data = download_from_s3(path)
    files = list_s3_files()

dag_instance = s3_example()
```

### 4. HttpHook

Make HTTP requests to external APIs.

```python
from airflow.providers.http.hooks.http import HttpHook
from airflow.decorators import dag, task
from datetime import datetime
import json

@dag(
    dag_id='http_hook_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def http_example():
    
    @task
    def call_api():
        """Call external API"""
        hook = HttpHook(
            method='GET',
            http_conn_id='http_default'
        )
        
        # Make GET request
        response = hook.run(
            endpoint='api/v1/data',
            headers={'Content-Type': 'application/json'},
            extra_options={'timeout': 30}
        )
        
        data = response.json()
        print(f"API Response: {data}")
        return data
    
    @task
    def post_to_api(data):
        """POST data to API"""
        hook = HttpHook(
            method='POST',
            http_conn_id='http_default'
        )
        
        payload = {'processed_data': data}
        
        response = hook.run(
            endpoint='api/v1/results',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"POST Response: {response.status_code}")
        return response.json()
    
    data = call_api()
    post_to_api(data)

dag_instance = http_example()
```

### 5. SlackHook

Send messages to Slack.

```python
from airflow.providers.slack.hooks.slack import SlackHook
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='slack_hook_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def slack_example():
    
    @task
    def send_slack_notification():
        """Send notification to Slack"""
        hook = SlackHook(slack_conn_id='slack_default')
        
        # Send message
        hook.call(
            api_method='chat.postMessage',
            json={
                'channel': '#data-pipeline',
                'text': 'Pipeline completed successfully! :tada:',
                'username': 'Airflow Bot'
            }
        )
        
        print("Slack notification sent")
    
    @task
    def send_slack_file():
        """Upload file to Slack"""
        hook = SlackHook(slack_conn_id='slack_default')
        
        # Upload file
        hook.call(
            api_method='files.upload',
            files={'file': open('/tmp/report.txt', 'rb')},
            data={
                'channels': '#data-pipeline',
                'title': 'Daily Report',
                'initial_comment': 'Here is today\'s report'
            }
        )
        
        print("File uploaded to Slack")
    
    send_slack_notification()
    send_slack_file()

dag_instance = slack_example()
```

## Creating Custom Hooks

### Basic Custom Hook

```python
from airflow.hooks.base import BaseHook
from typing import Any, Dict
import requests

class CustomApiHook(BaseHook):
    """
    Custom hook for interacting with a specific API
    """
    
    def __init__(self, conn_id: str = 'custom_api_default'):
        super().__init__()
        self.conn_id = conn_id
        self.connection = self.get_connection(conn_id)
    
    def get_conn(self):
        """
        Return connection object
        """
        return requests.Session()
    
    def get_data(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        """
        Get data from API endpoint
        """
        session = self.get_conn()
        
        url = f"{self.connection.host}/{endpoint}"
        
        # Add authentication
        headers = {
            'Authorization': f'Bearer {self.connection.password}',
            'Content-Type': 'application/json'
        }
        
        response = session.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def post_data(self, endpoint: str, data: Dict[str, Any]) -> Dict:
        """
        Post data to API endpoint
        """
        session = self.get_conn()
        
        url = f"{self.connection.host}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {self.connection.password}',
            'Content-Type': 'application/json'
        }
        
        response = session.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        return response.json()

# Usage
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id='custom_hook_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def custom_hook_example():
    
    @task
    def use_custom_hook():
        hook = CustomApiHook(conn_id='my_api')
        
        # Get data
        data = hook.get_data('users', params={'active': True})
        print(f"Retrieved {len(data)} users")
        
        # Post data
        result = hook.post_data('analytics', {'event': 'pipeline_run'})
        print(f"Posted analytics: {result}")
        
        return data
    
    use_custom_hook()

dag_instance = custom_hook_example()
```

### Advanced Custom Hook with Connection Pooling

```python
from airflow.hooks.base import BaseHook
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool

class PooledPostgresHook(BaseHook):
    """
    PostgreSQL Hook with connection pooling
    """
    
    _connection_pool = None
    
    def __init__(self, postgres_conn_id: str = 'postgres_default'):
        super().__init__()
        self.postgres_conn_id = postgres_conn_id
        self.connection = self.get_connection(postgres_conn_id)
        
        if PooledPostgresHook._connection_pool is None:
            self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        PooledPostgresHook._connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            host=self.connection.host,
            port=self.connection.port,
            database=self.connection.schema,
            user=self.connection.login,
            password=self.connection.password
        )
        self.log.info("Connection pool initialized")
    
    @contextmanager
    def get_conn(self):
        """
        Get connection from pool
        """
        conn = PooledPostgresHook._connection_pool.getconn()
        try:
            yield conn
        finally:
            PooledPostgresHook._connection_pool.putconn(conn)
    
    def execute_query(self, sql: str, params: tuple = None):
        """
        Execute query using pooled connection
        """
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            results = cursor.fetchall()
            cursor.close()
            conn.commit()
            return results
```

## Hook Best Practices

### 1. Use Context Managers

```python
# ✅ Good: Use context manager for connections
@task
def good_connection_handling():
    hook = PostgresHook(postgres_conn_id='postgres_default')
    
    with hook.get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        results = cursor.fetchall()
        cursor.close()
    
    return results

# ❌ Bad: Manual connection management
@task
def bad_connection_handling():
    hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = hook.get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
    # Forgot to close cursor and connection!
    return results
```

### 2. Handle Errors Gracefully

```python
@task
def robust_hook_usage():
    hook = S3Hook(aws_conn_id='aws_default')
    
    try:
        # Attempt operation
        data = hook.read_key(
            key='data/file.json',
            bucket_name='my-bucket'
        )
        return json.loads(data)
    
    except hook.get_conn().exceptions.NoSuchKey:
        # Handle specific error
        print("File not found, using default")
        return {'default': True}
    
    except Exception as e:
        # Handle general errors
        print(f"Error reading from S3: {e}")
        raise
```

### 3. Reuse Hooks

```python
@task
def reuse_hook_efficiently():
    """Reuse hook instance for multiple operations"""
    hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Multiple operations with same hook
    users = hook.get_records("SELECT * FROM users")
    orders = hook.get_records("SELECT * FROM orders")
    products = hook.get_records("SELECT * FROM products")
    
    return {
        'users': len(users),
        'orders': len(orders),
        'products': len(products)
    }
```

### 4. Use Bulk Operations

```python
@task
def bulk_insert_with_hook():
    """Use bulk operations for better performance"""
    hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Prepare bulk data
    records = [
        (1, 'Alice', 'alice@example.com'),
        (2, 'Bob', 'bob@example.com'),
        (3, 'Charlie', 'charlie@example.com')
    ]
    
    # Bulk insert
    hook.insert_rows(
        table='users',
        rows=records,
        target_fields=['id', 'name', 'email'],
        commit_every=1000
    )
    
    print(f"Inserted {len(records)} records")
```

## Advanced Patterns

### 1. Hook with Retry Logic

```python
from airflow.decorators import task
from tenacity import retry, stop_after_attempt, wait_exponential

@task
def hook_with_retry():
    """Use retry decorator for resilient operations"""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def fetch_data_with_retry():
        hook = HttpHook(http_conn_id='http_default')
        response = hook.run(endpoint='api/data')
        return response.json()
    
    return fetch_data_with_retry()
```

### 2. Multiple Hooks in One Task

```python
@task
def transfer_data_between_systems():
    """Transfer data from MySQL to PostgreSQL"""
    
    # Source hook
    mysql_hook = MySqlHook(mysql_conn_id='mysql_default')
    
    # Destination hook
    postgres_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Extract from MySQL
    data = mysql_hook.get_records("SELECT * FROM source_table")
    
    # Load to PostgreSQL
    postgres_hook.insert_rows(
        table='destination_table',
        rows=data,
        target_fields=['col1', 'col2', 'col3']
    )
    
    print(f"Transferred {len(data)} records")
```

### 3. Hook Factory Pattern

```python
from typing import Union
from airflow.hooks.base import BaseHook

class HookFactory:
    """Factory for creating appropriate hooks"""
    
    @staticmethod
    def get_database_hook(conn_id: str) -> Union[PostgresHook, MySqlHook]:
        """Get appropriate database hook based on connection type"""
        connection = BaseHook.get_connection(conn_id)
        
        if connection.conn_type == 'postgres':
            return PostgresHook(postgres_conn_id=conn_id)
        elif connection.conn_type == 'mysql':
            return MySqlHook(mysql_conn_id=conn_id)
        else:
            raise ValueError(f"Unsupported connection type: {connection.conn_type}")

@task
def use_hook_factory():
    """Use factory to get appropriate hook"""
    hook = HookFactory.get_database_hook('my_database')
    data = hook.get_records("SELECT * FROM table")
    return data
```

## Complete Example: ETL with Multiple Hooks

```python
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.slack.hooks.slack import SlackHook
from datetime import datetime
import json
import pandas as pd

@dag(
    dag_id='etl_with_hooks',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['etl', 'hooks']
)
def etl_pipeline_with_hooks():
    
    @task
    def extract_from_postgres():
        """Extract data from PostgreSQL"""
        hook = PostgresHook(postgres_conn_id='postgres_default')
        
        sql = """
            SELECT id, name, value, created_at
            FROM transactions
            WHERE DATE(created_at) = %s
        """
        
        records = hook.get_records(sql, parameters=['{{ ds }}'])
        
        # Convert to list of dicts
        data = [
            {
                'id': r[0],
                'name': r[1],
                'value': r[2],
                'created_at': r[3].isoformat()
            }
            for r in records
        ]
        
        print(f"Extracted {len(data)} records")
        return data
    
    @task
    def transform_data(data):
        """Transform extracted data"""
        df = pd.DataFrame(data)
        
        # Perform transformations
        df['value_usd'] = df['value'] * 1.1  # Example transformation
        df['processed_at'] = datetime.now().isoformat()
        
        transformed = df.to_dict('records')
        print(f"Transformed {len(transformed)} records")
        
        return transformed
    
    @task
    def load_to_s3(data):
        """Load transformed data to S3"""
        hook = S3Hook(aws_conn_id='aws_default')
        
        # Convert to JSON
        json_data = json.dumps(data, indent=2)
        
        # Upload to S3
        key = f"processed/{{ ds }}/transactions.json"
        hook.load_string(
            string_data=json_data,
            key=key,
            bucket_name='my-data-bucket',
            replace=True
        )
        
        s3_path = f"s3://my-data-bucket/{key}"
        print(f"Loaded data to {s3_path}")
        
        return {
            'path': s3_path,
            'record_count': len(data)
        }
    
    @task
    def send_notification(result):
        """Send completion notification to Slack"""
        hook = SlackHook(slack_conn_id='slack_default')
        
        message = f"""
        :white_check_mark: ETL Pipeline Completed
        
        Date: {{ ds }}
        Records Processed: {result['record_count']}
        Output Location: {result['path']}
        """
        
        hook.call(
            api_method='chat.postMessage',
            json={
                'channel': '#data-pipeline',
                'text': message,
                'username': 'Airflow ETL Bot'
            }
        )
        
        print("Notification sent to Slack")
    
    # Define pipeline
    raw_data = extract_from_postgres()
    transformed_data = transform_data(raw_data)
    result = load_to_s3(transformed_data)
    send_notification(result)

dag_instance = etl_pipeline_with_hooks()
```

## Additional Resources

- [Hooks Documentation](https://airflow.apache.org/docs/apache-airflow/stable/concepts/connections.html)
- [Provider Hooks](https://airflow.apache.org/docs/apache-airflow-providers/)
- [Custom Hooks Guide](https://airflow.apache.org/docs/apache-airflow/stable/howto/custom-operator.html#hooks)
- [Connection Management](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html)