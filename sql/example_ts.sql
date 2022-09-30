
#beach person counts
INSERT INTO (dataset_id,m_date,m_type,m_tag,m_value) ts_obs VALUES ('folly6thavenue','2022-09-29T13:00:00Z','person',NULL,4)

#json?
{"dataset_id":"folly6thavenue", "time": "2022-09-29T13:00:00Z", "m_type":"person", "m_tag":"",  "m_value": 4}


#bird counts
INSERT INTO (dataset_id,m_date,m_type,m_tag,m_value) ts_obs VALUES ('northinlet','2022-09-29T13:00:00Z','bird','gull',6)

#rain guage - measurement_type(m_type) suffixed with unit of measure
INSERT INTO (dataset_id,m_date,m_type,m_tag,m_value) ts_obs VALUES ('rosemontpeonie','2022-09-29T13:00:00Z','rain:inches',NULL,0.11)


#riptide? could use m_tag or m_value or both
INSERT INTO (dataset_id,m_date,m_type,m_tag,m_value) ts_obs VALUES ('follybeach','2022-09-29T13:00:00Z','riptide_flag','high_hazard',3)


#not sure if want to hold off on handling these for now?
#parking car counts - m_type using tracking_id suffixed(:) to object type, entrance/exit:id tag with 'm_tag' column
INSERT INTO (dataset_id,m_date,m_type,m_tag,m_value) ts_obs VALUES ('ioppark','2022-09-29T13:00:00Z','car:551','entrance:1',1)
INSERT INTO (dataset_id,m_date,m_type,m_tag,m_value) ts_obs VALUES ('ioppark','2022-09-29T13:00:00Z','car:663','exit:1',1)

#deepsort tracking includes several other fields, but tracking id is the main one of interest
#https://github.com/nathanrooy/rpi-urban-mobility-tracker/blob/490323abd7cb533331f61a83cbd3bf92e51ac6fd/umt/umt_main.py#L86