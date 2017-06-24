# pybj
Apply a ticket to bj

# Usage

```bash
usage: pybj.py [-h] [-d DATE] [-t RETRY] [-s] [-f FILE]

optional arguments:
  -h, --help            show this help message and exit
  -d DATE, --date DATE  The date you will enter: tomorrow <= yyyy-mm-dd <=
                        today + 4days. Default tomorrow.
  -t RETRY, --retry RETRY
                        Retry times: retry times if fail. Default 0
  -s, --skip_check_env_grade
                        Add this flag means you want to skip check_env_grade
                        from server, and the env_grade will be read from
                        conf.ini. This flag is made to decrease the
                        probability of being refused when the traffic is too
                        large. I recommend you check from server for the first
                        time, to make sure you fill in the right one.
  -f FILE, --file FILE  Path to config file. Default ./conf.ini
```



# TODO
crack sign