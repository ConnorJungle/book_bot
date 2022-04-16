from airflow.operators.python_operator import PythonOperator
# The DAG object; we'll need this to instantiate a DAG
from airflow import DAG

# Operators; we need this to operate!
from airflow.operators.bash import BashOperator
import datetime

def run_van_parks_advance_booking_bot(course, group_size, username, password,
                                  early_time, late_time, fallback,
                                  booking_fee, group_id, test=False):

    from bookbot import Booking

    import calendar

    today = datetime.date.today() #reference point.

    booking_date = today + datetime.timedelta(days=30)

    booker = Booking(username = username, password = password, test = test)

    ### run through group sizes in descending order to get the biggest possible group tee time
    ### run through the possible days first
    ### use try to catch use cases without breaking script
    ### takes aproximately 16 seconds to load and book
    _ = booker.get_vancouver_parks_times(course=course,
                                           days_in_advance=30,
                                           early_time=early_time,
                                           group_size=group_size,
                                           late_time=late_time,
                                           fallback=fallback,
                                           booking_fee=booking_fee,
                                           group=group_id)

def get_accounts():
     return [
                dict(
                    course = 'mccleery',
                    group_size = 4,
                    username = 'connorjjung@gmail.com',
                    password = 'hockey1995',
                    early_time = '8:30',
                    late_time = '9:45',
                    fallback = False,
                    booking_fee = True,
                    group_id=1
                ),
                # dict(
                #     course = 'mccleery',
                #     group_size = 4,
                #     username = 'conjungle95@gmail.com',
                #     password = 'hockey1995',
                #     early_time = '8:30', # 9 minutes between tee times
                #     late_time = '9:45',
                #     fallback = False,
                #     booking_fee = True,
                #     group_id=2
                # )
            ]

def book_group(number, account):
    #load the values if needed in the command you plan to execute
    return PythonOperator(
                task_id=f'run_van_parks_advance_booking_bot_{number}',
                provide_context=True,
                python_callable=run_van_parks_advance_booking_bot,
                op_kwargs=account,
                dag=dag,
            )
# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization
default_args={
    'depends_on_past': False,
    'email': ['connorjjung@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
}

with DAG(
    'van_parks_advance_booking_bot',
    ### Need to find a way to match UTC time to Pacific time
    default_args=default_args,
    description='Run the book bot to book N tee times back to back for N groups',
    schedule_interval="* 13 * * 4,5", # “At 22:00 on Friday and Saturday.”
    start_date=datetime.datetime(2022, 4, 7),
    catchup=False,
    tags=['back to back', 'golf', 'vancouver parks', 'weekend', 'groups'],
    max_active_runs=2,
) as dag:

    ### arguments for booking weekend cancellation tee times
    job_start = BashOperator(
                    task_id='start',
                    bash_command='date',
                    dag=dag)

    all_done = BashOperator(
                    task_id='end',
                    bash_command='date',
                    dag=dag)

    bookings = [ book_group(i, account_info) for i, account_info in enumerate(get_accounts()) ]
    ### declare DAG order / using list comprehension to run these in parallel
    job_start >> bookings >> all_done

    ### Loop over accounts to produce parralel runs
    # for i, account_info in enumerate(get_accounts()):
    #     job_start >> book_group(i, account_info) >> all_done
