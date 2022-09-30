

CREATE TABLE public.ts_obs (
    row_id integer NOT NULL,
    row_update_date timestamp without time zone DEFAULT now(),
    dataset_id character varying(30),
    m_date timestamp without time zone,
    m_type character varying(30),
    m_tag  character varying(30),
    m_value double precision
);


ALTER TABLE public.ts_obs OWNER TO postgres;

CREATE SEQUENCE public.ts_obs_row_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ts_obs_row_id_seq OWNER TO postgres;

ALTER SEQUENCE public.ts_obs_row_id_seq OWNED BY public.ts_obs.row_id;

ALTER TABLE ONLY public.ts_obs ALTER COLUMN row_id SET DEFAULT nextval('public.ts_obs_row_id_seq'::regclass);

CREATE UNIQUE INDEX i_ts_obs ON public.ts_obs USING btree (dataset_id, m_date, m_type, m_tag);


