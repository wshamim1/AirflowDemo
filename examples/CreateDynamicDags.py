from datetime import timedelta
import pandas as pd
import requests
import json
from requests.exceptions import RequestException, ConnectionError
import time
import mysql.connector
import logging
import random
import airflow
from airflow.models import DAG
from airflow.models import Variable
from airflow.operators.bash_operator import BashOperator
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.dagrun_operator import TriggerDagRunOperator
from airflow.operators.subdag_operator import SubDagOperator
from datetime import datetime
from airflow import AirflowException
from airflow.models import Variable

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dag_config = Variable.get("test_Variables_Config", deserialize_json=True)
SDC_URL = dag_config["SDC_URL"]
push_url = dag_config["PUSH_NOTFCTN"]
sleep_interval = dag_config["SLEEP_INTERVAL"]
SDC_USERNAME = dag_config["SDC_USERNAME"]
SDC_PWD = dag_config["SDC_PWD"]
MAX_ACTIVE_RUN = dag_config["MAX_ACTIVE_RUN"]
SCHEMA = dag_config["SCHEMA_NAME"]
userAuthDetails = '{"userName":"' + SDC_USERNAME + '", "password":"' + SDC_PWD + '"}'
authHeader = {"X-Requested-By": "SCH", "Content-Type": "application/json"}
sch = 'SCH'
contenttype = 'application/json'
restcall = 'true'

metadata_connection_host = dag_config["METADATA_DB"]
metadata_connection_username = dag_config["METADATA_DB_USERNAME"]
metadata_connection_password = dag_config["METADATA_DB_PASSWORD"]
metadata_connection_db = dag_config["METADATA_DB_CONNECTION"]


def createMysqlConnection():
    connection = mysql.connector.connect(user=metadata_connection_username, password=metadata_connection_password,
                                         host=metadata_connection_host,
                                         database=metadata_connection_db)
    return connection


def getJobStatus(JOBID):
    statusqry = "select  case when coalesce (B.ERROR_MESSAGE, C.ERROR_MESSAGE) is NULL then  " \
                "'SUCCESS' else 'FAILED' end as STATUS from jobrunner.JOB A inner join jobrunner.JOB_STATUS B  on  " \
                "A.ID =B.JOB_ID left outer join   (select C.JOB_STATUS_ID,GROUP_CONCAT(C.MESSAGE SEPARATOR ', ') " \
                "as ERROR_MESSAGE from jobrunner.JOB_STATUS_HISTORY C where C.MESSAGE like '%ERROR%' group by C.JOB_STATUS_ID) " \
                "C on B.ID =C.JOB_STATUS_ID where A.ID= '" + JOBID + "' order by B.RUN_COUNT desc " \
                                                                     "limit 1"
    print('------------')
    print(statusqry)
    print('------------')

    connection = createMysqlConnection()
    print(connection)
    cursor = connection.cursor()
    cursor.execute(statusqry)
    record = cursor.fetchall()
    cursor.close()
    connection.close()
    return record[0][0]


def insertTaskData(context, userinpid, dag_name):
    connection = createMysqlConnection()
    cursor = connection.cursor()
    dag_run = context.get('dag_run')
    task_instances = dag_run.get_task_instances()

    print(task_instances)
    print(len(task_instances))
    for ti in task_instances:
        task_name = ti.task_id
        if ti.state == None:
            state = 'None'
        else:
            state = ti.state

        start_date = ti.start_date
        end_date = ti.end_date
        execution_date = ti.execution_date
        # userinpid=2

        inserttaskq = "insert into " + SCHEMA + ".test_AIRFLOWTaskStatus values('" + str(
            userinpid) + "','" + dag_name + "','" + task_name + "','" + state + "','" + str(start_date) + "','" + str(
            end_date) + "','" + str(execution_date) + "')"
        cursor.execute(inserttaskq)
        connection.commit()
    cursor.close()
    connection.close()

def updateTaskData1(context, userinpid, dag_name, state1):
    connection = createMysqlConnection()
    cursor = connection.cursor()
    dag_run = context.get('dag_run')
    task_instances = dag_run.get_task_instances()

    print(task_instances)
    print(len(task_instances))
    for ti in task_instances:
        task_name = ti.task_id
        if ti.state == None:
            state = 'None'
        else:
            state = ti.state

        start_date = ti.start_date
        end_date = ti.end_date
        execution_date = ti.execution_date

        updatetasks = "update  " + SCHEMA + ".test_AIRFLOWTaskStatus set STATUS='" + state + "', " \
                                                                                             "start_date = '" + str(
            start_date) + "', " \
                          "end_date = '" + str(end_date) + "'" \
                                                           " where test_USRINP_ID='" + str(userinpid) + "' and " \
                                                                                                        " EXECUTION_DATE='" + str(
            execution_date) + "' and " \
                              " TASK_NAME = '" + task_name + "' and  status not in ('success')"
        print(updatetasks)

        cursor.execute(updatetasks)
        connection.commit()
    cursor.close()
    connection.close()
    upstream_states = [ti.state for ti in task_instances]
    print(upstream_states)
    if 'failed' in upstream_states:
        raise AirflowException("Failing task because one or more upstream tasks failed.")


def updateTaskData(task_name, state, start_date, end_date, execution_date, userinpid):
    connection = createMysqlConnection()
    cursor = connection.cursor()
    e_date = str(datetime.strptime(str(execution_date), '%Y-%m-%dT%H:%M:%S+00:00')) + "+00:00"
    updatetasks = "update  " + SCHEMA + ".test_AIRFLOWTaskStatus set STATUS='" + state + "', " \
                                                                                         "start_date = '" + str(
        start_date) + "', " \
                      "end_date = '" + str(end_date) + "'" \
                                                       " where test_USRINP_ID='" + str(userinpid) + "' and " \
                                                                                                    " EXECUTION_DATE='" + e_date + "' and " \
                                                                                                                                   " TASK_NAME = '" + task_name + "'"
    print(updatetasks)

    cursor.execute(updatetasks)
    connection.commit()
    cursor.close()
    connection.close()

def on_failure_callback(context):
    print('In the failuer callback')
    print(context['userinpid'])

    # insertTaskData(context)
    task_name = context['task_instance'].task_id

    start_date = context['task_instance'].start_date
    end_date = context['task_instance'].end_date
    execution_date = context['task_instance'].execution_date
    state = 'failed'
    userinpid = context['userinpid']

    # updateTaskData(task_name, state, start_date, end_date, execution_date, userinpid)
    updateTaskData1(context, userinpid, dag_id, state)


def on_success_callback(context):
    print('on success...')
    print(context['userinpid'])

    task_name = context['task_instance'].task_id

    start_date = context['task_instance'].start_date
    end_date = context['task_instance'].end_date
    state = context['task_instance'].state
    execution_date = context['task_instance'].execution_date
    state = 'success'
    userinpid = context['userinpid']

    # updateTaskData(task_name,state,start_date,end_date,execution_date,userinpid)
    updateTaskData1(context, userinpid, dagname, state)


def streamset_jobdetails(**kwargs):
    task_name = kwargs['task_instance'].task_id

    start_date = kwargs['task_instance'].start_date
    end_date = kwargs['task_instance'].end_date
    execution_date = kwargs['task_instance'].execution_date
    state = kwargs['task_instance'].state
    userinpid = kwargs['userinpid']
    user_uiid = kwargs['user_uiid']
    dag_name = kwargs['dag_name']
    print(dag_name)
    print(userinpid)

    print('calling... st 1' + dagname)
    print(str(userinpid))
    print(dag_id)
    print(dag_number)
    # updateTaskData(task_name, state, start_date, end_date, execution_date, userinpid)
    updateTaskData1(kwargs, userinpid, dagname, state)

    print('Starting job....')
    jid = kwargs['jobid']

    print(jid)
    print(SDC_URL + 'security/public-rest/v1/authentication/login')

    runtimeparam = "select PARAM_VAL_STACKED from " + SCHEMA + ".V_test_JOB_PARAMETERS_LF where JOB_ID='" + str(jid) + "'"
    connection = createMysqlConnection()
    cursor = connection.cursor()
    cursor.execute(runtimeparam)
    record = cursor.fetchall()
    cursor.close()
    connection.close()
    print(record[0][0])
    paramval = record[0][0]
    print(jid)
    startjoburl = url = SDC_URL + 'jobrunner/rest/v1/job/' + str(jid) + '/start'
    print(startjoburl)
    try:
        get_n_update_strt_version(user_uiid=str(userinpid), job_id=str(jid))
        responce = requests.post(url=SDC_URL + 'security/public-rest/v1/authentication/login',
                                 data=userAuthDetails,
                                 headers=authHeader).headers
        print(responce)
        token = responce['X-SS-User-Auth-Token']
        print("\"" + token + "\"")

        tokenHeader = {'X-Requested-By': sch, 'Content-Type': contenttype, 'X-SS-REST-CALL': restcall,
                       'X-SS-User-Auth-Token': token}
        startjob = requests.post(startjoburl, data=paramval,
                                 headers=tokenHeader).json()
        print("---" + str(startjob))
    except Exception as err:
        update_version_error(user_uiid=str(userinpid), job_id=str(jid))
        raise AirflowException('An Error occured in the pipeline')
    while True:
        jobstatus = requests.get(url=SDC_URL + 'jobrunner/rest/v1/job/' + str(jid) + '/currentStatus',
                                 headers=tokenHeader).json()
        print(jobstatus)
        status = jobstatus['status']
        if status == 'ACTIVE' or status == 'DEACTIVATING':
            print('job : ' + jid + ' is still active...')
            sleep_range = random.randint(15, 60)
            print('sleeping for {} seconds...'.format(sleep_range))
            time.sleep(sleep_range)
        if status == 'INACTIVE':
            stat = getJobStatus(jid)
            print('======')
            print(stat)
            if str(stat).strip() == 'FAILED':
                print('job failed....')
                update_version_error(user_uiid=str(userinpid), job_id=str(jid))
                raise AirflowException('An Error occured in the pipeline')
            else:
                update_version_complete(user_uiid=str(userinpid), job_id=str(jid))
            break


def startTasks(**kwargs):
    print('starting airflow tasks...')
    userinpid = kwargs['userinpid']
    dag_name = kwargs['dag_name']
    print(dag_name)
    print(userinpid)
    print('------')
    insertTaskData(kwargs, userinpid, dag_name)
    get_n_update_strt_version(user_uiid=str(userinpid))


def EndTasks(**kwargs):
    print('starting airflow tasks...')
    userinpid = kwargs['userinpid']
    user_uiid = kwargs['user_uiid']
    dag_name = kwargs['dag_name']
    print(dag_name)
    print(userinpid)
    print('------')
    update_version_complete(user_uiid=str(userinpid))
    updateTaskData1(kwargs, userinpid, dag_name, '')


def get_n_update_strt_version(user_uiid=None, job_id=None):
    logger.info("Printing JobID:- {}".format(job_id))
    if job_id is None:
        for j in range(0, 3):
            try:
                vapi_response = requests.post(url=push_url + '/api/events/jobs/external/' + user_uiid + '/start',
                                              verify=False)
                logger.info(vapi_response)
                if vapi_response.status_code == 200:
                    logger.info(vapi_response)
                    vapi_response_obj = vapi_response.json()
                    logger.info(vapi_response)
                    version_number = vapi_response_obj['version']['versionNumber']
                    logger.info("version created {}".format(version_number))
                elif vapi_response.status_code == 404:
                    # Need to raise the Airflow exception when all testing is done.
                    raise Exception("UserID not registered from UI side")
                elif vapi_response.status_code == 409:
                    raise Exception("Job is already running")
                elif vapi_response.status_code == 500:
                    raise RequestException("Internal server error")
            except (RequestException, ConnectionError) as err:
                logger.info("Not able to get run verion ID")
                logger.info(str(err))
                logger.info("Trying after {} seconds. Try --> {}...........".format(sleep_interval, j + 1))
                time.sleep(sleep_interval)
                if j != 2:
                    continue
                logger.info("Reached max retries. Not starting the Jobs")
                raise AirflowException('Notification API is down')
            except Exception as e:
                logger.info(str(e))
            break
    else:
        try:
            vapi_response = requests.post(url=push_url + '/api/events/jobs/external/' + user_uiid + '/steps/' + job_id
                                              + '/start', verify=False)
            if vapi_response.status_code == 200:
                logger.info(vapi_response)
                vapi_response_obj = vapi_response.json()
                logger.info(vapi_response)
                version_number = vapi_response_obj['version']['versionNumber']
                logger.info("version created {}".format(version_number))
            elif vapi_response.status_code == 404:
                raise Exception("UserID/job_id not registered from UI side")
            elif vapi_response.status_code == 500:
                raise RequestException("Internal server error")
        except (RequestException, ConnectionError) as err:
            logger.info("Not able to update the step")
            logger.info(str(err))
        except Exception as e:
            logger.info(str(e))


def update_version_complete(user_uiid=None, job_id=None):
    logger.info("Printing JobID:- {}".format(job_id))
    if job_id is None:
        for j in range(0, 3):
            try:
                vapi_response = requests.post(url=push_url + '/api/events/jobs/external/' + user_uiid + '/complete',
                                              verify=False)
                if vapi_response.status_code == 200:
                    logger.info(vapi_response)
                    vapi_response_obj = vapi_response.json()
                    logger.info(vapi_response)
                    version_number = vapi_response_obj['version']['versionNumber']
                    logger.info("version created {}".format(version_number))
                elif vapi_response.status_code == 404:
                    raise Exception("UserID/job_id not registered from UI side")
                elif vapi_response.status_code == 500:
                    raise RequestException("Internal server error")
            except (RequestException, ConnectionError) as err:
                logger.info("Not able to update")
                logger.info(str(err))
                logger.info("Trying after {} seconds. Try --> {}...........".format(sleep_interval, j + 1))
                time.sleep(sleep_interval)
                continue
            except Exception as e:
                logger.info(str(e))
            break
    else:
        try:
            vapi_response = requests.post(url=push_url + '/api/events/jobs/external/' + user_uiid + '/steps/' + job_id
                                              + '/complete', verify=False)
            if vapi_response.status_code == 200:
                logger.info(vapi_response)
                vapi_response_obj = vapi_response.json()
                logger.info(vapi_response)
                version_number = vapi_response_obj['version']['versionNumber']
                logger.info("version created {}".format(version_number))
            elif vapi_response.status_code == 404:
                raise Exception("UserID/job_id not registered from UI side")
            elif vapi_response.status_code == 500:
                raise RequestException("Internal server error")
        except (RequestException, ConnectionError) as err:
            logger.info("Not able to update the step")
            logger.info(str(err))
        except Exception as e:
            logger.info(str(e))


def update_version_error(user_uiid=None, job_id=None):
    logger.info("Printing JobID:- {}".format(job_id))
    if job_id is None:
        for j in range(0, 3):
            try:
                vapi_response = requests.post(url=push_url + '/api/events/jobs/external/' + user_uiid + '/error',
                                              verify=False)
                if vapi_response.status_code == 200:
                    vapi_response_obj = json.loads(vapi_response.json())
                    version_number = vapi_response_obj['version']['versionNumber']
                    logger.info("version created {}".format(version_number))
                elif vapi_response.status_code == 404:
                    raise Exception("UserID/job_id not registered from UI side")
                elif vapi_response.status_code == 500:
                    raise RequestException("Internal server error")
            except (RequestException, ConnectionError) as err:
                logger.info("Not able to update error for jobs")
                logger.info(str(err))
                logger.info("Trying after {} seconds. Try --> {}...........".format(sleep_interval, j + 1))
                time.sleep(sleep_interval)
                continue
            except Exception as e:
                logger.info(str(e))
            break
    else:
        try:
            vapi_response = requests.post(url=push_url + '/api/events/jobs/external/' + user_uiid + '/steps/' + job_id
                                              + '/error', verify=False)
            if vapi_response.status_code == 200:
                vapi_response_obj = json.loads(vapi_response.json())
                version_number = vapi_response_obj['version']['versionNumber']
                logger.info("version created {}".format(version_number))
            elif vapi_response.status_code == 404:
                raise Exception("UserID/job_id not registered from UI side")
            elif vapi_response.status_code == 500:
                raise RequestException("Internal server error")
        except (RequestException, ConnectionError) as err:
            logger.info("Not able to update the error for step")
            logger.info(str(err))
        except Exception as e:
            logger.info(str(e))


def Dummy(**kwargs):
    print('Dummy invoked..')


def create_dag(dag_id, schedule, dag_number, default_args, is_active_flag, user_uiid):
    userinpid = dag_number
    query = "select * from " + SCHEMA + ".V_test_JOB_PARAMETERS_LF where test_USRINP_ID='" + str(
        dag_number) + "' order by TABLE_NM"

    dag = DAG(dag_id, schedule_interval=schedule, default_args=default_args, max_active_runs=MAX_ACTIVE_RUN, is_paused_upon_creation=is_active_flag)

    start_task = PythonOperator(task_id='start_task', python_callable=startTasks,
                                op_kwargs={'dag_name': dag_id, 'userinpid': userinpid, 'user_uiid': user_uiid},
                                provide_context=True,
                                pool='streamsetpool',
                                on_failure_callback=on_failure_callback,
                                on_success_callback=on_success_callback,
                                dag=dag)
    final_task = PythonOperator(task_id='End_Task', trigger_rule='all_done', python_callable=EndTasks,
                                op_kwargs={'dag_name': dag_id, 'userinpid': userinpid, 'user_uiid': user_uiid},
                                provide_context=True,
                                pool='streamsetpool',
                                on_failure_callback=on_failure_callback,
                                on_success_callback=on_success_callback,
                                dag=dag
                                )

    conn = createMysqlConnection()
    df = pd.read_sql(query, conn)
    pd.set_option('display.expand_frame_repr', False)
    df['jobid_jobname'] = df['JOB_ID'].str.cat(df['JOB_NAME'], sep="___")
    TABLE_NM_GRP = df.groupby('TABLE_NM')
    conn.close()
    with dag:
        d11 = PythonOperator(task_id='task_update',
                             python_callable=Dummy,
                             op_kwargs={'userinpid': userinpid}, pool='streamsetpool',
                             provide_context=True,
                             on_failure_callback=on_failure_callback,
                             on_success_callback=on_success_callback
                             )
        d12 = PythonOperator(task_id='task_update1',
                             trigger_rule='none_skipped',
                             python_callable=Dummy,
                             op_kwargs={'userinpid': userinpid}, pool='streamsetpool',
                             provide_context=True,
                             on_failure_callback=on_failure_callback,
                             on_success_callback=on_success_callback
                             )

        for tablename, data in TABLE_NM_GRP:

            d1 = PythonOperator(task_id='task_{0}'.format(tablename),
                                python_callable=Dummy,
                                op_kwargs={'userinpid': userinpid}, pool='streamsetpool',
                                provide_context=True,
                                on_failure_callback=on_failure_callback,
                                on_success_callback=on_success_callback
                                )

            final_counter = 0
            d2 = []
            for i, jid_name in enumerate(data['jobid_jobname']):
                d2.append(PythonOperator(task_id='{0}'.format((jid_name.split('___')[1])),
                                         execution_timeout=timedelta(hours=3),
                                         python_callable=streamset_jobdetails,
                                         pool='streamsetpool',
                                         op_kwargs={'jobid': (jid_name.split('___')[0]), 'userinpid': userinpid,
                                                    'dag_name': dag_id, 'user_uiid': user_uiid},
                                         on_failure_callback=on_failure_callback,
                                         on_success_callback=on_success_callback,
                                         provide_context=True))

                final_counter = i
                if i == 0:
                    start_task >> d1 >> d11 >> d2[0]

                else:
                    d2[i - 1] >> d2[i]

            d2[final_counter] >> d12 >> final_task


    return dag


connection = createMysqlConnection()

print(connection)
cursor = connection.cursor()
cursor.execute('select * from ' + SCHEMA + '.test_USER_INPUT')
record = cursor.fetchall()
for row in record:
    dag_inactive_flag = True
    appname = row[2]
    srcsystemname = row[3]
    srcsystemtype = row[4]
    tgtsystemname = row[7]
    tgtsystemtype = row[8]
    userinpid = row[0]
    user_uiid = row[1]
    cron_string = row[9]
    is_create_dag = row[10]
    is_active = row[11]
    schedule_date_time = row[16]
    if is_create_dag is None or is_create_dag == 0:
        continue
    if is_active is not None and is_active == 1:
        dag_inactive_flag = False
    schedule = str(cron_string)
    dagname = str(appname) + '__' + str(srcsystemname) + '__' + str(srcsystemtype) + '__' + str(tgtsystemname) + '__' + str(tgtsystemtype) + '__' + str(userinpid)

    dag_id = dagname

    default_args = {'owner': 'airflow',
                    'start_date': schedule_date_time
                    }

    dag_number = userinpid
    returnddag = create_dag(dag_id,
                            schedule,
                            dag_number,
                            default_args,dag_inactive_flag, user_uiid)

    print('-------------')
    print(returnddag)
    print('--------------')
    insertq = "insert into " + SCHEMA + ".test_AIRFLOWDAGS (test_USRINP_ID, DAG_NAME, DAG_SCHEDULE, DAG_CRTN_DATE) values(" \
                                        "'" + str(dag_number) + "','" + dag_id + "','" + schedule + "','" + str(datetime.now()) + "')" \
                                                                                                               " on duplicate key update dag_name='" + dag_id + "'"
    cursor.execute(insertq)
    connection.commit()
    print("record inserted ..." + str(cursor.rowcount))
    globals()[dag_id] = returnddag
cursor.close()
connection.close()

