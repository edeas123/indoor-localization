select *
from ( 
select user_id, record_time, ssid, bssid, concat(substring(bssid, 1,16), 0) as base_bssid, level, freq  
from SHED10.wifi
where (ssid like 'uofs-%' or ssid = 'eduroam')) as t1
where t1.user_id=777;