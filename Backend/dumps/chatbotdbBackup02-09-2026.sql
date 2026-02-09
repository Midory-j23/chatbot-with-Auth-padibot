--
-- PostgreSQL database dump
--

\restrict vb1HXdZXTiPvlbHlJymbyrxaS6MlGldzlFW4ga56E6fJHqfLLC3Bf60KW95jxcD

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

-- Started on 2026-02-09 12:06:58

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 224 (class 1259 OID 24654)
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: mohammad
--

CREATE TABLE public.chat_messages (
    id integer NOT NULL,
    session_id integer,
    sender text,
    message text,
    created_at timestamp without time zone DEFAULT now(),
    CONSTRAINT chat_messages_sender_check CHECK ((sender = ANY (ARRAY['user'::text, 'assistant'::text])))
);


ALTER TABLE public.chat_messages OWNER TO mohammad;

--
-- TOC entry 223 (class 1259 OID 24653)
-- Name: chat_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: mohammad
--

CREATE SEQUENCE public.chat_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chat_messages_id_seq OWNER TO mohammad;

--
-- TOC entry 4940 (class 0 OID 0)
-- Dependencies: 223
-- Name: chat_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mohammad
--

ALTER SEQUENCE public.chat_messages_id_seq OWNED BY public.chat_messages.id;


--
-- TOC entry 222 (class 1259 OID 24607)
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: mohammad
--

CREATE TABLE public.chat_sessions (
    id integer NOT NULL,
    user_id integer,
    title text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.chat_sessions OWNER TO mohammad;

--
-- TOC entry 221 (class 1259 OID 24606)
-- Name: chat_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: mohammad
--

CREATE SEQUENCE public.chat_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chat_sessions_id_seq OWNER TO mohammad;

--
-- TOC entry 4941 (class 0 OID 0)
-- Dependencies: 221
-- Name: chat_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mohammad
--

ALTER SEQUENCE public.chat_sessions_id_seq OWNED BY public.chat_sessions.id;


--
-- TOC entry 220 (class 1259 OID 24591)
-- Name: users; Type: TABLE; Schema: public; Owner: mohammad
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying,
    hashed_password character varying,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.users OWNER TO mohammad;

--
-- TOC entry 219 (class 1259 OID 24590)
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: mohammad
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO mohammad;

--
-- TOC entry 4942 (class 0 OID 0)
-- Dependencies: 219
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mohammad
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- TOC entry 4771 (class 2604 OID 24657)
-- Name: chat_messages id; Type: DEFAULT; Schema: public; Owner: mohammad
--

ALTER TABLE ONLY public.chat_messages ALTER COLUMN id SET DEFAULT nextval('public.chat_messages_id_seq'::regclass);


--
-- TOC entry 4768 (class 2604 OID 24610)
-- Name: chat_sessions id; Type: DEFAULT; Schema: public; Owner: mohammad
--

ALTER TABLE ONLY public.chat_sessions ALTER COLUMN id SET DEFAULT nextval('public.chat_sessions_id_seq'::regclass);


--
-- TOC entry 4765 (class 2604 OID 24594)
-- Name: users id; Type: DEFAULT; Schema: public; Owner: mohammad
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- TOC entry 4934 (class 0 OID 24654)
-- Dependencies: 224
-- Data for Name: chat_messages; Type: TABLE DATA; Schema: public; Owner: mohammad
--

COPY public.chat_messages (id, session_id, sender, message, created_at) FROM stdin;
\.


--
-- TOC entry 4932 (class 0 OID 24607)
-- Dependencies: 222
-- Data for Name: chat_sessions; Type: TABLE DATA; Schema: public; Owner: mohammad
--

COPY public.chat_sessions (id, user_id, title, created_at, updated_at) FROM stdin;
\.


--
-- TOC entry 4930 (class 0 OID 24591)
-- Dependencies: 220
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: mohammad
--

COPY public.users (id, email, hashed_password, is_active, created_at) FROM stdin;
\.


--
-- TOC entry 4943 (class 0 OID 0)
-- Dependencies: 223
-- Name: chat_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mohammad
--

SELECT pg_catalog.setval('public.chat_messages_id_seq', 1, false);


--
-- TOC entry 4944 (class 0 OID 0)
-- Dependencies: 221
-- Name: chat_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mohammad
--

SELECT pg_catalog.setval('public.chat_sessions_id_seq', 1, false);


--
-- TOC entry 4945 (class 0 OID 0)
-- Dependencies: 219
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: mohammad
--

SELECT pg_catalog.setval('public.users_id_seq', 1, false);


--
-- TOC entry 4779 (class 2606 OID 24665)
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: mohammad
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- TOC entry 4777 (class 2606 OID 24615)
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: mohammad
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- TOC entry 4775 (class 2606 OID 24605)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: mohammad
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4781 (class 2606 OID 24666)
-- Name: chat_messages chat_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mohammad
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- TOC entry 4780 (class 2606 OID 24635)
-- Name: chat_sessions fk_chat_sessions_user; Type: FK CONSTRAINT; Schema: public; Owner: mohammad
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT fk_chat_sessions_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE NOT VALID;


-- Completed on 2026-02-09 12:06:59

--
-- PostgreSQL database dump complete
--

\unrestrict vb1HXdZXTiPvlbHlJymbyrxaS6MlGldzlFW4ga56E6fJHqfLLC3Bf60KW95jxcD

