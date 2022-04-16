from airflow.operators.python_operator import PythonOperator
# The DAG object; we'll need this to instantiate a DAG
from airflow import DAG

# Operators; we need this to operate!
from airflow.operators.dummy_operator import DummyOperator
from airflow.utils.trigger_rule import TriggerRule

import datetime

def run_vancouver_parks_weekend_bot(group_sizes, username, password,
                                 early_time, late_time, fallback, booking_fee,
                                 test=False):

    from bookbot import Booking

    import calendar

    today = datetime.date.today() #reference point.

    friday = today + datetime.timedelta((calendar.FRIDAY-today.weekday()) % 7 )
    saturday = today + datetime.timedelta((calendar.SATURDAY-today.weekday()) % 7 )
    sunday = today + datetime.timedelta((calendar.SUNDAY-today.weekday()) % 7 )

    weekend_dates = [friday, saturday, sunday]
    days_to_weekend = [
        datetime.timedelta((calendar.FRIDAY-today.weekday()) % 7 ).days, ### add this for long weekend fridays
        datetime.timedelta((calendar.SATURDAY-today.weekday()) % 7 ).days,
        datetime.timedelta((calendar.SUNDAY-today.weekday()) % 7 ).days
    ]

    van_courses = ['mccleery', 'fraserview', 'langara']

    booker = Booking(username = username, password = password, test = test)

    ### run through group sizes in descending order to get the biggest possible group tee time
    for group_size in sorted(group_sizes)[::-1]:
        ### run through the possible days first
        for days, date in zip(days_to_weekend, weekend_dates):
            ### iterate through the courses
            for course in van_courses:
                print(course, date)
            #     try:
                    ### use try to catch use cases without breaking script
                ### takes aproximately 16 seconds to load and book
                success = booker.get_vancouver_parks_times(course=course,
                                                           days_in_advance=days,
                                                           early_time=early_time,
                                                           group_size=group_size,
                                                           late_time=late_time,
                                                           fallback=fallback,
                                                           booking_fee=booking_fee)

                if success:
                    ### if we successfully booked on the day, we move on to the next day
                    break

# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization
default_args={
    'depends_on_past': False,
    'email': ['connorjjung@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
}

with DAG(
    'van_parks_weekend_cancelation_bot',
    # These args will get passed on to each operator
    # You can override them on a per-task basis during operator initialization
    default_args=default_args,
    description='Run the book bot every 5 minutes to scan Weekend tee times for early cancellations',
#     schedule_interval=timedelta(minutes=5),
    schedule_interval="*/5 * * * *",
    start_date=datetime.datetime(2022, 4, 5),
    catchup=False,
    tags=['vancouver', 'golf', 'vancouver parks', 'weekend', 'cancelation'],
) as dag:

    ### arguments for booking weekend cancellation tee times
    ### if we have more accounts we  can kick off parralel jobs
    group_sizes = [4,3,2]
    username = 'connorjjung@gmail.com'
    password = 'hockey1995'
    early_time = '7:45'
    late_time = '11:15' # requires military time
    fallback = False
    booking_fee = False

    job_start = DummyOperator(task_id="job_start", dag=dag)
    all_done = DummyOperator(task_id="all_done", trigger_rule=TriggerRule.NONE_FAILED, dag=dag)

    job = PythonOperator(
    task_id='run_vancouver_parks_weekend_bot',
    provide_context=True,
    python_callable=run_vancouver_parks_weekend_bot,
    op_kwargs={"group_sizes" : group_sizes, "username" : username, "password" : password,
                "early_time" : early_time, "late_time" : late_time, "fallback" : fallback, "booking_fee" : booking_fee},
    dag=dag,
)

    job_start >> job >> all_done
