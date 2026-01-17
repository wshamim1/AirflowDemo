# Airflow Variables and Connections

Variables and Connections are key features in Airflow for managing configuration, credentials, and external system connections.

## Variables

Variables are a generic way to store and retrieve arbitrary content or settings as key-value pairs in Airflow's metadata database.

### Creating Variables

#### Via UI
1. Navigate to Admin → Variables
2. Click "+" to add a new variable
3. Enter Key and Value
4. Click Save

#### Via CLI
```bash
# Set a variable
airflow variables set my_key my_value

# Set from JSON file
airflow variables set my_config --json '{"key1": "value1", "key2": "value2"}'

# Import from file
airflow variables import variables.json
```

#### Programmatically
```python
from airflow.models import Variable

# Set variable
Variable.set("my_key", "my_value")

# Set JSON variable
Variable.set("my_config", {"key1": "value1", "key2": "value2"}, serialize_json=True)
```

### Using Variables in DAGs

#### Method 1: Variable.get()

```python
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from datetime import datetime

def use_variable(**kwargs):
    # Get simple variable
    api_key = Variable.get("api_key")
    print(f"API Key: {api_key}")
    
    # Get with default value
    timeout = Variable.get("timeout", default_var=30)
    print(f"Timeout: {timeout}")
    
    # Get JSON variable
    config = Variable.get("app_config", deserialize_json=True)
    print(f"Config: {config}")
    
    return api_key

dag = DAG(
    dag_id='variables_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

task = PythonOperator(
    task_id='use_variable',
    python_callable=use_variable,
    dag=dag
)
```

#### Method 2: Jinja Templates

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

dag = DAG(
    dag_id='variables_template_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

# Use variable in template
task = BashOperator(
    task_id='use_variable_template',
    bash_command='echo "API URL: {{ var.value.api_url }}"',
    dag=dag
)

# Use JSON variable in template
task2 = BashOperator(
    task_id='use_json_variable',
    bash_command='echo "Environment: {{ var.json.app_config.environment }}"',
    dag=dag
)
```

#### Method 3: TaskFlow API

```python
from airflow.decorators import dag, task
from airflow.models import Variable
from datetime import datetime

@dag(
    dag_id='variables_taskflow',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def variables_taskflow_example():
    
    @task
    def get_config():
        """Get configuration from Variables"""
        config = Variable.get("app_config", deserialize_json=True)
        return config
    
    @task
    def use_config(config):
        """Use configuration"""
        print(f"Environment: {config.get('environment')}")
        print(f"Debug Mode: {config.get('debug')}")
        return config['environment']
    
    config = get_config()
    use_config(config)

dag_instance = variables_taskflow_example()
```

### Best Practices for Variables

#### 1. Use Environment-Specific Variables

```python
from airflow.models import Variable

@task
def get_environment_config():
    """Get configuration based on environment"""
    env = Variable.get("environment", default_var="dev")
    
    if env == "prod":
        config = Variable.get("prod_config", deserialize_json=True)
    else:
        config = Variable.get("dev_config", deserialize_json=True)
    
    return config
```

#### 2. Cache Variables at DAG Parse Time

```python
from airflow import DAG
from airflow.models import Variable
from datetime import datetime

# ✅ Good: Get variable once at DAG parse time
API_URL = Variable.get("api_url")

dag = DAG(
    dag_id='cached_variable',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)

# ❌ Bad: Getting variable in every task execution
def bad_practice(**kwargs):
    api_url = Variable.get("api_url")  # Queries DB every time
    # Use api_url
```

#### 3. Use JSON for Complex Configurations

```python
# Store complex config as JSON
config = {
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "mydb"
    },
    "api": {
        "url": "https://api.example.com",
        "timeout": 30
    },
    "features": {
        "enable_cache": True,
        "max_retries": 3
    }
}

Variable.set("app_config", config, serialize_json=True)

# Use in DAG
@task
def use_complex_config():
    config = Variable.get("app_config", deserialize_json=True)
    db_host = config['database']['host']
    api_url = config['api']['url']
    return config
```

#### 4. Secure Sensitive Variables

```python
# Variables with these prefixes are automatically masked in logs
# and UI: password, secret, passwd, authorization, api_key, apikey, access_token

Variable.set("api_key_secret", "sk-1234567890")  # Will be masked
Variable.set("database_password", "mypassword")  # Will be masked
```

---

## Connections

Connections store information about external systems (databases, APIs, cloud services) including credentials and connection parameters.

### Creating Connections

#### Via UI
1. Navigate to Admin → Connections
2. Click "+" to add a new connection
3. Fill in connection details:
   - Connection Id
   - Connection Type
   - Host
   - Schema/Database
   - Login
   - Password
   - Port
   - Extra (JSON)

#### Via CLI
```bash
# Add connection
airflow connections add 'my_postgres' \
    --conn-type 'postgres' \
    --conn-host 'localhost' \
    --conn-schema 'mydb' \
    --conn-login 'user' \
    --conn-password 'password' \
    --conn-port 5432

# Export connections
airflow connections export connections.json

# Import connections
airflow connections import connections.json
```

#### Via Environment Variables
```bash
# Format: AIRFLOW_CONN_{CONN_ID}
export AIRFLOW_CONN_MY_POSTGRES='postgresql://user:password@localhost:5432/mydb'
export AIRFLOW_CONN_MY_API='http://user:password@api.example.com:80'
```

#### Programmatically
```python
from airflow.models import Connection
from airflow import settings

# Create connection
conn = Connection(
    conn_id='my_postgres',
    conn_type='postgres',
    host='localhost',
    schema='mydb',
    login='user',
    password='password',
    port=5432
)

# Add to session
session = settings.Session()
session.add(conn)
session.commit()
```

### Using Connections in DAGs

#### With Hooks

```python
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime

@dag(
    dag_id='connection_with_hook',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def connection_example():
    
    @task
    def query_database():
        """Query database using connection"""
        # Hook automatically uses the connection
        hook = PostgresHook(postgres_conn_id='my_postgres')
        
        records = hook.get_records("SELECT * FROM users LIMIT 10")
        print(f"Found {len(records)} records")
        
        return records
    
    query_database()

dag_instance = connection_example()
```

#### Accessing Connection Details

```python
from airflow.hooks.base import BaseHook
from airflow.decorators import task

@task
def use_connection_details():
    """Access connection details directly"""
    conn = BaseHook.get_connection('my_api')
    
    # Access connection properties
    host = conn.host
    port = conn.port
    login = conn.login
    password = conn.password
    schema = conn.schema
    
    # Access extra parameters (JSON)
    extra = conn.extra_dejson
    api_key = extra.get('api_key')
    
    print(f"Connecting to {host}:{port}")
    
    return {
        'host': host,
        'port': port
    }
```

### Common Connection Types

#### 1. PostgreSQL Connection

```python
from airflow.providers.postgres.hooks.postgres import PostgresHook

@task
def postgres_example():
    hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Execute query
    records = hook.get_records("SELECT * FROM users")
    
    # Insert data
    hook.insert_rows(
        table='users',
        rows=[(1, 'Alice'), (2, 'Bob')],
        target_fields=['id', 'name']
    )
    
    return records
```

#### 2. MySQL Connection

```python
from airflow.providers.mysql.hooks.mysql import MySqlHook

@task
def mysql_example():
    hook = MySqlHook(mysql_conn_id='mysql_default')
    
    # Get pandas DataFrame
    df = hook.get_pandas_df("SELECT * FROM products")
    
    return df.to_dict('records')
```

#### 3. AWS Connection

```python
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

@task
def aws_example():
    # Connection should have:
    # - Login: AWS Access Key ID
    # - Password: AWS Secret Access Key
    # - Extra: {"region_name": "us-east-1"}
    
    hook = S3Hook(aws_conn_id='aws_default')
    
    # List buckets
    buckets = hook.list_buckets()
    print(f"Found {len(buckets)} buckets")
    
    return buckets
```

#### 4. HTTP/API Connection

```python
from airflow.providers.http.hooks.http import HttpHook

@task
def api_example():
    # Connection should have:
    # - Host: https://api.example.com
    # - Extra: {"api_key": "your-key"}
    
    hook = HttpHook(http_conn_id='api_default')
    
    response = hook.run(
        endpoint='v1/data',
        headers={'Authorization': 'Bearer token'}
    )
    
    return response.json()
```

#### 5. SSH Connection

```python
from airflow.providers.ssh.hooks.ssh import SSHHook

@task
def ssh_example():
    hook = SSHHook(ssh_conn_id='ssh_default')
    
    # Execute command
    result = hook.exec_ssh_client_command('ls -la /data')
    
    print(f"Command output: {result}")
    return result
```

### Connection with Extra Parameters

```python
# Store additional configuration in Extra field (JSON)
extra_config = {
    "api_key": "sk-1234567890",
    "timeout": 30,
    "max_retries": 3,
    "region": "us-east-1",
    "ssl_verify": True
}

# Access in code
from airflow.hooks.base import BaseHook

@task
def use_extra_params():
    conn = BaseHook.get_connection('my_api')
    extra = conn.extra_dejson
    
    api_key = extra.get('api_key')
    timeout = extra.get('timeout', 30)
    region = extra.get('region', 'us-east-1')
    
    print(f"Using API key: {api_key[:10]}...")
    print(f"Timeout: {timeout}s")
    print(f"Region: {region}")
```

## Advanced Patterns

### 1. Dynamic Connection Selection

```python
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import Variable
from datetime import datetime

@dag(
    dag_id='dynamic_connection',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False
)
def dynamic_connection_example():
    
    @task
    def query_appropriate_database():
        """Select database based on environment"""
        env = Variable.get("environment", default_var="dev")
        
        # Choose connection based on environment
        if env == "prod":
            conn_id = "postgres_prod"
        else:
            conn_id = "postgres_dev"
        
        hook = PostgresHook(postgres_conn_id=conn_id)
        records = hook.get_records("SELECT COUNT(*) FROM users")
        
        print(f"Environment: {env}, Records: {records[0][0]}")
        return records
    
    query_appropriate_database()

dag_instance = dynamic_connection_example()
```

### 2. Connection Testing

```python
@task
def test_connection():
    """Test if connection is working"""
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    
    try:
        hook = PostgresHook(postgres_conn_id='postgres_default')
        hook.get_records("SELECT 1")
        print("Connection successful!")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
```

### 3. Multiple Connections in One Task

```python
@task
def transfer_data():
    """Transfer data between two databases"""
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    from airflow.providers.mysql.hooks.mysql import MySqlHook
    
    # Source connection
    source_hook = MySqlHook(mysql_conn_id='mysql_source')
    
    # Destination connection
    dest_hook = PostgresHook(postgres_conn_id='postgres_dest')
    
    # Extract from source
    data = source_hook.get_records("SELECT * FROM source_table")
    
    # Load to destination
    dest_hook.insert_rows(
        table='dest_table',
        rows=data,
        target_fields=['col1', 'col2', 'col3']
    )
    
    print(f"Transferred {len(data)} records")
```

## Security Best Practices

### 1. Use Secrets Backend

Configure Airflow to use external secrets manager:

```python
# airflow.cfg
[secrets]
backend = airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
backend_kwargs = {"connections_prefix": "airflow/connections", "variables_prefix": "airflow/variables"}
```

### 2. Encrypt Sensitive Data

```python
# Airflow automatically encrypts passwords in connections
# Ensure fernet_key is set in airflow.cfg

# Variables with sensitive names are masked
Variable.set("api_key_secret", "sensitive-value")  # Masked in UI/logs
Variable.set("password", "sensitive-value")  # Masked in UI/logs
```

### 3. Use Environment Variables for Local Development

```bash
# .env file
export AIRFLOW_VAR_API_KEY=your-api-key
export AIRFLOW_CONN_MY_DB=postgresql://user:pass@localhost/db
```

### 4. Rotate Credentials Regularly

```python
@task
def rotate_credentials():
    """Update connection with new credentials"""
    from airflow.models import Connection
    from airflow import settings
    
    # Get existing connection
    session = settings.Session()
    conn = session.query(Connection).filter(
        Connection.conn_id == 'my_api'
    ).first()
    
    # Update password
    conn.password = get_new_password()  # Your logic here
    
    session.commit()
    print("Credentials rotated successfully")
```

## Complete Example: Configuration Management

```python
from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.hooks.base import BaseHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from datetime import datetime
import json

@dag(
    dag_id='config_management_example',
    start_date=datetime(2024, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['config', 'example']
)
def config_management():
    
    @task
    def load_configuration():
        """Load all configuration"""
        # Get environment
        env = Variable.get("environment", default_var="dev")
        
        # Get app config
        app_config = Variable.get("app_config", deserialize_json=True)
        
        # Get database connection details
        db_conn = BaseHook.get_connection('postgres_default')
        
        # Get S3 connection details
        s3_conn = BaseHook.get_connection('aws_default')
        
        config = {
            'environment': env,
            'app': app_config,
            'database': {
                'host': db_conn.host,
                'port': db_conn.port,
                'schema': db_conn.schema
            },
            's3': {
                'region': s3_conn.extra_dejson.get('region_name', 'us-east-1')
            }
        }
        
        print(f"Configuration loaded for environment: {env}")
        return config
    
    @task
    def extract_data(config):
        """Extract data using configuration"""
        hook = PostgresHook(postgres_conn_id='postgres_default')
        
        sql = f"SELECT * FROM {config['app']['source_table']}"
        records = hook.get_records(sql)
        
        print(f"Extracted {len(records)} records")
        return records
    
    @task
    def upload_to_s3(data, config):
        """Upload data to S3"""
        hook = S3Hook(aws_conn_id='aws_default')
        
        # Convert to JSON
        json_data = json.dumps(data, default=str)
        
        # Upload
        bucket = config['app']['s3_bucket']
        key = f"data/{{ ds }}/output.json"
        
        hook.load_string(
            string_data=json_data,
            key=key,
            bucket_name=bucket,
            replace=True
        )
        
        print(f"Uploaded to s3://{bucket}/{key}")
        return f"s3://{bucket}/{key}"
    
    @task
    def log_completion(s3_path, config):
        """Log completion"""
        print(f"""
        Pipeline completed successfully!
        Environment: {config['environment']}
        Output: {s3_path}
        """)
    
    # Define pipeline
    config = load_configuration()
    data = extract_data(config)
    s3_path = upload_to_s3(data, config)
    log_completion(s3_path, config)

dag_instance = config_management()
```

## Troubleshooting

### Variable Not Found
```python
# Use default value
value = Variable.get("my_var", default_var="default_value")
```

### Connection Not Found
```python
from airflow.exceptions import AirflowNotFoundException

try:
    conn = BaseHook.get_connection('my_conn')
except AirflowNotFoundException:
    print("Connection not found, using defaults")
    # Use default configuration
```

### JSON Parsing Error
```python
# Safely parse JSON variable
try:
    config = Variable.get("config", deserialize_json=True)
except json.JSONDecodeError:
    print("Invalid JSON, using default config")
    config = {}
```

## Additional Resources

- [Variables Documentation](https://airflow.apache.org/docs/apache-airflow/stable/concepts/variables.html)
- [Connections Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html)
- [Secrets Backend](https://airflow.apache.org/docs/apache-airflow/stable/security/secrets/secrets-backend/index.html)
- [Managing Connections](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html)