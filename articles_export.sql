--
-- PostgreSQL database dump
--

\restrict JPXuWigmS0FyKV3vN6bLtnbvNaGcdoF6wf07Vb7aeiOQfyTh1CbHzpoHKxahZOm

-- Dumped from database version 17.10 (Debian 17.10-1.pgdg12+1)
-- Dumped by pg_dump version 17.10 (Debian 17.10-1.pgdg12+1)

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
-- Name: article_relations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.article_relations (
    source_article_id uuid NOT NULL,
    target_article_id uuid NOT NULL,
    sort_order integer NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.article_relations OWNER TO postgres;

--
-- Name: article_revision_relations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.article_revision_relations (
    revision_id uuid NOT NULL,
    target_article_id uuid NOT NULL,
    sort_order integer NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.article_revision_relations OWNER TO postgres;

--
-- Name: article_revision_tags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.article_revision_tags (
    revision_id uuid NOT NULL,
    tag_id uuid NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.article_revision_tags OWNER TO postgres;

--
-- Name: article_revisions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.article_revisions (
    article_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    content text,
    seo_title character varying(255),
    seo_description text,
    seo_keywords character varying(255),
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    revision_no integer NOT NULL,
    status public.revision_status_enum NOT NULL,
    slug character varying(255) NOT NULL,
    short_description text,
    category_id uuid,
    banner_image_id uuid,
    author_id uuid NOT NULL,
    locked_by uuid,
    locked_at timestamp with time zone,
    seo_canonical character varying(255),
    seo_robots character varying(50),
    seo_og_image_id uuid
);


ALTER TABLE public.article_revisions OWNER TO postgres;

--
-- Name: article_tags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.article_tags (
    article_id uuid NOT NULL,
    tag_id uuid NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.article_tags OWNER TO postgres;

--
-- Name: article_versions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.article_versions (
    article_id uuid NOT NULL,
    version integer NOT NULL,
    schema_version character varying(50) NOT NULL,
    snapshot_hash character varying(64) NOT NULL,
    snapshot_json json NOT NULL,
    published_by uuid,
    published_at timestamp with time zone NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.article_versions OWNER TO postgres;

--
-- Name: article_workflow_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.article_workflow_logs (
    id uuid NOT NULL,
    article_id uuid NOT NULL,
    action public.workflow_action_enum NOT NULL,
    from_status public.article_status_enum,
    to_status public.article_status_enum,
    action_by uuid,
    comment text,
    meta_data json,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.article_workflow_logs OWNER TO postgres;

--
-- Name: articles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.articles (
    category_id uuid,
    title character varying(255) NOT NULL,
    slug character varying(255) NOT NULL,
    content text,
    is_featured boolean NOT NULL,
    status public.article_status_enum NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    seo_title character varying(255),
    seo_description text,
    seo_keywords character varying(255),
    seo_canonical character varying(255),
    seo_robots character varying(50),
    seo_og_image_id uuid,
    short_description text,
    banner_image_id uuid,
    visibility public.visibility_level_enum NOT NULL,
    author_id uuid NOT NULL,
    is_pinned boolean NOT NULL,
    content_hash character varying(64),
    version integer NOT NULL,
    locked_by uuid,
    locked_at timestamp with time zone,
    translation_group_id uuid,
    locale character varying(10) NOT NULL,
    reading_time integer NOT NULL,
    word_count integer NOT NULL,
    approved_by uuid,
    rejection_reason text,
    published_at timestamp with time zone,
    scheduled_publish_at timestamp with time zone,
    scheduled_unpublish_at timestamp with time zone,
    tts_voices json
);


ALTER TABLE public.articles OWNER TO postgres;

--
-- Name: tags; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tags (
    name character varying(100) NOT NULL,
    slug character varying(150) NOT NULL,
    description text,
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.tags OWNER TO postgres;

--
-- Data for Name: article_relations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.article_relations (source_article_id, target_article_id, sort_order, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: article_revision_relations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.article_revision_relations (revision_id, target_article_id, sort_order, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: article_revision_tags; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.article_revision_tags (revision_id, tag_id, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: article_revisions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.article_revisions (article_id, title, content, seo_title, seo_description, seo_keywords, id, created_at, updated_at, revision_no, status, slug, short_description, category_id, banner_image_id, author_id, locked_by, locked_at, seo_canonical, seo_robots, seo_og_image_id) FROM stdin;
\.


--
-- Data for Name: article_tags; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.article_tags (article_id, tag_id, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: article_versions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.article_versions (article_id, version, schema_version, snapshot_hash, snapshot_json, published_by, published_at, id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: article_workflow_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.article_workflow_logs (id, article_id, action, from_status, to_status, action_by, comment, meta_data, created_at, updated_at) FROM stdin;
408a69a8-11cb-4772-8f5f-977ec33a407a	15859c70-ddc0-4c66-b282-0d84a9bfa099	SUBMIT	DRAFT	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:32:04.866545+00	2026-06-28 16:32:04.867149+00
08d184fe-0438-4425-9384-a9cd6a66e951	15859c70-ddc0-4c66-b282-0d84a9bfa099	REJECT	PENDING	REJECTED	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	Not enough content	null	2026-06-28 16:32:04.890485+00	2026-06-28 16:32:04.890628+00
f7c5a230-4ad2-41c1-86f1-ee62641fab23	15859c70-ddc0-4c66-b282-0d84a9bfa099	RESUBMIT	REJECTED	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:32:04.900776+00	2026-06-28 16:32:04.900905+00
94dda824-79ec-4267-8690-b48b3d60e8fd	15859c70-ddc0-4c66-b282-0d84a9bfa099	SCHEDULE	PENDING	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	{"old_schedule": null, "new_schedule": "2026-06-29T16:32:04.908845+00:00"}	2026-06-28 16:32:04.916508+00	2026-06-28 16:32:04.916632+00
f91a09d7-98e1-4b12-a10b-1900d3b4aa6c	988a8a51-27ac-4d4d-91ec-ee41fb5a74ba	SUBMIT	DRAFT	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:32:27.327307+00	2026-06-28 16:32:27.328089+00
9b75f90d-d436-4c4b-9973-3f9ad8c9272a	988a8a51-27ac-4d4d-91ec-ee41fb5a74ba	REJECT	PENDING	REJECTED	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	Not enough content	null	2026-06-28 16:32:27.355736+00	2026-06-28 16:32:27.355917+00
d81ef742-4a2c-438b-a9f9-c902d3bae009	988a8a51-27ac-4d4d-91ec-ee41fb5a74ba	RESUBMIT	REJECTED	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:32:27.373256+00	2026-06-28 16:32:27.373419+00
162520b2-3dc1-41c3-8a5f-808ecf7b2c28	988a8a51-27ac-4d4d-91ec-ee41fb5a74ba	SCHEDULE	PENDING	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	{"old_schedule": null, "new_schedule": "2026-06-29T16:32:27.381032+00:00"}	2026-06-28 16:32:27.390614+00	2026-06-28 16:32:27.390785+00
b5a8159a-9e79-4253-996d-e4c654ec6755	988a8a51-27ac-4d4d-91ec-ee41fb5a74ba	APPROVE	PENDING	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	Approved but scheduled for 2026-06-29T16:32:27.381032+00:00	null	2026-06-28 16:32:27.415556+00	2026-06-28 16:32:27.415784+00
410fbfcc-7d0f-46f9-8c27-23671f1bb368	988a8a51-27ac-4d4d-91ec-ee41fb5a74ba	PUBLISH	PENDING	PUBLISHED	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:32:27.428746+00	2026-06-28 16:32:27.428907+00
cfff249b-8638-4a1e-adc0-813a09a8f980	988a8a51-27ac-4d4d-91ec-ee41fb5a74ba	UNPUBLISH	PUBLISHED	DRAFT	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:32:27.440971+00	2026-06-28 16:32:27.441123+00
1681e4b9-273b-4210-9388-2a5844f35cfe	946fe790-22ae-40a3-b08c-9c858c902b0d	SUBMIT	DRAFT	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:34:03.736356+00	2026-06-28 16:34:03.737031+00
33179f7b-3609-41e8-be82-317ba1addbd2	946fe790-22ae-40a3-b08c-9c858c902b0d	REJECT	PENDING	REJECTED	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	Not enough content	null	2026-06-28 16:34:03.756132+00	2026-06-28 16:34:03.756286+00
0537b126-745c-4244-be95-6e769c7fe8c6	946fe790-22ae-40a3-b08c-9c858c902b0d	RESUBMIT	REJECTED	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:34:03.780719+00	2026-06-28 16:34:03.780884+00
3f8dccd1-3ca9-4b58-9a35-4b359dcb2763	946fe790-22ae-40a3-b08c-9c858c902b0d	SCHEDULE	PENDING	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	{"old_schedule": null, "new_schedule": "2026-06-29T16:34:03.790298+00:00"}	2026-06-28 16:34:03.800546+00	2026-06-28 16:34:03.800718+00
6c292425-4610-4427-9790-5fe3a06923e5	946fe790-22ae-40a3-b08c-9c858c902b0d	APPROVE	PENDING	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	Approved but scheduled for 2026-06-29T16:34:03.790298+00:00	null	2026-06-28 16:34:03.820398+00	2026-06-28 16:34:03.820547+00
6adb7f84-9d1b-44ed-a762-52e8d4f24b9d	946fe790-22ae-40a3-b08c-9c858c902b0d	PUBLISH	PENDING	PUBLISHED	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:34:03.86015+00	2026-06-28 16:34:03.860311+00
9860e537-f403-4b47-9026-b3ce7c87ee93	946fe790-22ae-40a3-b08c-9c858c902b0d	UNPUBLISH	PUBLISHED	DRAFT	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:34:03.876259+00	2026-06-28 16:34:03.87645+00
78c8a1cc-062b-4a77-a04e-55e262bb1e2f	96490026-89e6-4fb0-82ca-859f8e02bfc8	SUBMIT	DRAFT	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:39:00.267268+00	2026-06-28 16:39:00.267879+00
270266b9-2ce9-4b25-a351-36df230b9d64	96490026-89e6-4fb0-82ca-859f8e02bfc8	REJECT	PENDING	REJECTED	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	Not enough content	null	2026-06-28 16:39:00.293795+00	2026-06-28 16:39:00.29394+00
d724c37f-32c0-4ae3-83fa-865a5f510d34	96490026-89e6-4fb0-82ca-859f8e02bfc8	RESUBMIT	REJECTED	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:39:00.310391+00	2026-06-28 16:39:00.310569+00
5a784099-a2da-414d-afe0-bbad7cb7a4ef	96490026-89e6-4fb0-82ca-859f8e02bfc8	SCHEDULE	PENDING	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	{"old_schedule": null, "new_schedule": "2026-06-29T16:39:00.317963+00:00"}	2026-06-28 16:39:00.328399+00	2026-06-28 16:39:00.328568+00
e5b8830c-254d-42f9-99ca-65e0ba6b6ff2	96490026-89e6-4fb0-82ca-859f8e02bfc8	APPROVE	PENDING	PENDING	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	Approved but scheduled for 2026-06-29T16:39:00.317963+00:00	null	2026-06-28 16:39:00.34663+00	2026-06-28 16:39:00.346786+00
4e0a937f-26e8-4e2b-bc01-4f384d653261	96490026-89e6-4fb0-82ca-859f8e02bfc8	PUBLISH	PENDING	PUBLISHED	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:39:00.366641+00	2026-06-28 16:39:00.367151+00
5118d667-2c0a-45eb-8c8c-2d406de6fd8f	96490026-89e6-4fb0-82ca-859f8e02bfc8	UNPUBLISH	PUBLISHED	DRAFT	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	\N	null	2026-06-28 16:39:00.393294+00	2026-06-28 16:39:00.393421+00
4df52725-0589-4abd-802f-c68508d85419	ca6b73d3-1bfb-4f90-8827-9b80b2b9d6dc	SUBMIT	DRAFT	PENDING	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:14:03.842347+00	2026-06-29 01:14:03.843009+00
6e3810a5-fb9c-4af0-8423-7fdf0e44df06	ca6b73d3-1bfb-4f90-8827-9b80b2b9d6dc	PUBLISH	PENDING	PUBLISHED	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:14:03.882317+00	2026-06-29 01:14:03.882537+00
046f995f-6234-4ca2-bb6f-f2e5b8f487cf	de479b8d-3e77-4190-9af6-9e98e0b9b887	SUBMIT	DRAFT	PENDING	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:14:18.12006+00	2026-06-29 01:14:18.1207+00
457f8c07-ca7a-40a6-9552-c398908f4365	de479b8d-3e77-4190-9af6-9e98e0b9b887	PUBLISH	PENDING	PUBLISHED	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:14:18.142725+00	2026-06-29 01:14:18.142872+00
2207d908-1ff8-4d87-8f4e-04a134cd1f8f	955f4596-23b4-4558-a4b1-720525cf41ab	SUBMIT	DRAFT	PENDING	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:27:31.412997+00	2026-06-29 01:27:31.413954+00
61bf700f-1b90-443a-a0a9-67ac5d71138a	955f4596-23b4-4558-a4b1-720525cf41ab	PUBLISH	PENDING	PUBLISHED	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:27:31.436639+00	2026-06-29 01:27:31.436811+00
3c3fc382-dfaa-4c75-8c11-e073b69ddac6	0866e922-44b5-4b46-b208-fee3444b9814	SUBMIT	DRAFT	PENDING	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:27:51.566263+00	2026-06-29 01:27:51.567209+00
aa4471a9-c13f-4f6e-a9c8-908bef67c446	0866e922-44b5-4b46-b208-fee3444b9814	PUBLISH	PENDING	PUBLISHED	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:27:51.602252+00	2026-06-29 01:27:51.602401+00
f4952d02-b7b9-47a9-895a-8f034d9d43ba	5dbcb7d1-f7d2-433f-a2ee-be43b2633811	SUBMIT	DRAFT	PENDING	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:28:23.310853+00	2026-06-29 01:28:23.311497+00
c70e021f-91df-42d9-9e8e-9f6b098983e1	5dbcb7d1-f7d2-433f-a2ee-be43b2633811	PUBLISH	PENDING	PUBLISHED	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:28:23.342871+00	2026-06-29 01:28:23.343032+00
878c29f3-6979-42ef-ad8d-5a7f1076170c	13d993e7-4286-4851-bc6e-c6b5391b093e	SUBMIT	DRAFT	PENDING	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:30:26.154989+00	2026-06-29 01:30:26.155705+00
4914713e-2ec6-448c-b48f-dae73c251c0e	13d993e7-4286-4851-bc6e-c6b5391b093e	PUBLISH	PENDING	PUBLISHED	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:30:26.194089+00	2026-06-29 01:30:26.194255+00
994ee245-40af-473e-aeaf-553ea14598ab	b06c1052-8210-4ac6-ae6f-5106b51f0ecd	SUBMIT	DRAFT	PENDING	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:36:21.7123+00	2026-06-29 01:36:21.713021+00
579099c4-bbab-4f72-9e95-28a41d24412f	b06c1052-8210-4ac6-ae6f-5106b51f0ecd	PUBLISH	PENDING	PUBLISHED	4865719c-133f-4908-a9e3-8219fef46bd9	\N	null	2026-06-29 01:36:21.805915+00	2026-06-29 01:36:21.806369+00
\.


--
-- Data for Name: articles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.articles (category_id, title, slug, content, is_featured, status, id, created_at, updated_at, seo_title, seo_description, seo_keywords, seo_canonical, seo_robots, seo_og_image_id, short_description, banner_image_id, visibility, author_id, is_pinned, content_hash, version, locked_by, locked_at, translation_group_id, locale, reading_time, word_count, approved_by, rejection_reason, published_at, scheduled_publish_at, scheduled_unpublish_at, tts_voices) FROM stdin;
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 100 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-100-cong-nghe-khoa-hoc-may-tinh-bdd058	<p>Đây là nội dung chi tiết của bài viết mẫu số 100.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PUBLISHED	1bb2b1f3-2008-4e98-8abd-119261882fd0	2026-06-28 08:36:56.951488+00	2026-06-28 08:38:14.882859+00	Công nghệ & Khoa học Máy tính: Ứng dụng vào đời sống | Trường Kỹ thuật và Công nghệ - Đại học Vinh	Khám phá ứng dụng thực tế của công nghệ thông tin và khoa học máy tính trong thời đại số hóa. Bài viết mẫu số 100 từ Trường Kỹ thuật và Công nghệ - Đại học Vinh.	Công nghệ, Khoa học Máy tính, Ứng dụng công nghệ, Đại học Vinh, Trường Kỹ thuật và Công nghệ	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
9fb40836-26ff-41f6-b3d5-cb2e5bc229ba	Lời cảm ơn đến đơn vị tài trợ Công ty cổ phần Cảng quốc tế Việt - Lào	loi-cam-on-den-don-vi-tai-tro-cong-ty-co-phan-cang-quoc-te-viet-lao	<p style="text-align:justify;">Trong không khí chung vui cùng hội thi “Sinh viên với việc rèn luyện kỹ năng nghề nghiệp” của khoa Tài chính - Ngân hàng, trường Kinh tế, trường Đại học Vinh. Các giảng viên, các bạn sinh viên khoa Tài chính - Ngân hàng cũng như các thành viên trong câu lạc bộ FIC xin gửi lời cảm ơn chân thành đến đơn vị tài trợ là Công ty cổ phần Cảng quốc tế Việt - Lào đã hợp tác tài trợ cho chương trình “Sinh viên với việc rèn luyện kỹ năng nghề nghiệp” năm 2022.</p><p style="text-align:justify;">Công ty CP Cảng quốc tế Lào- Việt được thành lập ngày 26/12/1992, thực hiện quản lý, khai thác hai khu cảng chính là Cảng Vũng Áng và Cảng Xuân Hải có vị trí địa lý vô cùng thuận lợi, là cảng biển nước sâu mang tầm vóc một trong những cảng biển lớn nhất khu vực miền Trung Việt Nam, đã đóng vai trò phát triển kinh tế khu vực, tạo công ăn việc làm cho hàng trăm lao động trong và ngoài tỉnh Hà Tĩnh.</p><p style="text-align:justify;"><img class="image_resized" style="width:1138px;" src="https://eco.vinhuni.edu.vn/Upload/images/ANH_CHUNG/cangvungang-202292711185.jpg" alt=""></p><p style="text-align:justify;">Cảng Vũng Áng hiện là một khâu quan trọng trong chuỗi dịch vụ Logistics của Miền Trung Việt Nam và Hành lang Kinh tế Đông Tây, có vai trò quan trọng như một cửa ngõ chính ra biển Đông cho cả khu vực.</p><p style="text-align:justify;">Một lần nữa, chúng tôi xin được gửi lời cảm ơn tới đơn vị tài trợ cho chương trình và xin chúc Quý công ty ngày càng phát triển và thành công trong tương lai. Chúng tôi mong muốn, quan hệ giữa Quý Công ty và khoa Tài chính – Ngân hàng ngày càng phát triển bền vững trên cơ sở hai bên cùng có lợi.</p><p style="text-align:justify;">Chúng tôi cũng tin tưởng và hy vọng rằng trong thời gian tới tiếp tục nhận được sự quan tâm, giúp đỡ và hợp tác nhiều hơn nữa từ phía Quý công ty.</p>	t	PUBLISHED	98165bc2-45a7-4ab3-819b-3e7a07f531e6	2026-06-28 09:29:38.746896+00	2026-06-28 10:37:37.194699+00	Cảm ơn Công ty Cảng quốc tế Việt - Lào tài trợ hội thi...	Khoa Tài chính - Ngân hàng gửi lời cảm ơn sâu sắc đến Công ty Cảng quốc tế Việt - Lào đã tài trợ hội thi "Sinh viên với việc rèn luyện kỹ năng nghề nghiệp"...	cảm ơn, tài trợ, Cảng quốc tế Việt - Lào, kỹ năng nghề	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
242660fd-113e-43e2-9d51-5b6eff030fbb	đâsdaádaas	dasdaadaas	<p>dấdadasdadasd</p>	f	DRAFT	5967c700-8319-40e1-99be-e34614343566	2026-06-28 11:17:25.898086+00	2026-06-28 11:17:25.898094+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
242660fd-113e-43e2-9d51-5b6eff030fbb	dsds	dsds		f	DRAFT	b475b116-d0f9-49f3-993b-86842f309a4b	2026-06-28 11:29:49.267403+00	2026-06-28 11:30:10.788247+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 1 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-1-cong-nghe-khoa-hoc-may-tinh-8f6e61	<p>Đây là nội dung chi tiết của bài viết mẫu số 1.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PUBLISHED	28ed9600-a162-4b07-a746-4e46655a2f71	2026-06-28 08:36:56.766914+00	2026-06-28 08:36:56.766917+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 4 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-4-cong-nghe-khoa-hoc-may-tinh-d26b81	<p>Đây là nội dung chi tiết của bài viết mẫu số 4.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	ARCHIVED	e4b70ab6-c9d9-4d17-bee4-6271a36c7690	2026-06-28 08:36:56.786884+00	2026-06-28 08:36:56.786886+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 7 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-7-cong-nghe-khoa-hoc-may-tinh-ef854b	<p>Đây là nội dung chi tiết của bài viết mẫu số 7.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PUBLISHED	417c38bb-2968-46b7-83ac-592791ce8f0b	2026-06-28 08:36:56.794094+00	2026-06-28 08:36:56.794096+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 8 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-8-cong-nghe-khoa-hoc-may-tinh-f42170	<p>Đây là nội dung chi tiết của bài viết mẫu số 8.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PUBLISHED	89c3355c-bb53-41a5-befb-fa55be839d7f	2026-06-28 08:36:56.797434+00	2026-06-28 08:36:56.797436+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 9 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-9-cong-nghe-khoa-hoc-may-tinh-638295	<p>Đây là nội dung chi tiết của bài viết mẫu số 9.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	ARCHIVED	77a06f42-41d1-485f-9446-48704da98785	2026-06-28 08:36:56.799792+00	2026-06-28 08:36:56.799794+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 10 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-10-cong-nghe-khoa-hoc-may-tinh-bcfcbf	<p>Đây là nội dung chi tiết của bài viết mẫu số 10.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	c933192c-5b4a-4b9b-aea1-a40196508da1	2026-06-28 08:36:56.802139+00	2026-06-28 08:36:56.80214+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 11 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-11-cong-nghe-khoa-hoc-may-tinh-f4e455	<p>Đây là nội dung chi tiết của bài viết mẫu số 11.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	ARCHIVED	732566bf-27b4-4e10-9c1a-5246d53efcf7	2026-06-28 08:36:56.80414+00	2026-06-28 08:36:56.804141+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 12 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-12-cong-nghe-khoa-hoc-may-tinh-fb2e51	<p>Đây là nội dung chi tiết của bài viết mẫu số 12.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	ARCHIVED	57ad853b-f20c-4173-b518-29e2d6efd352	2026-06-28 08:36:56.805897+00	2026-06-28 08:36:56.805897+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 15 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-15-cong-nghe-khoa-hoc-may-tinh-22300f	<p>Đây là nội dung chi tiết của bài viết mẫu số 15.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	DRAFT	c0160079-6adb-42a1-800e-8872b73e76ad	2026-06-28 08:36:56.813703+00	2026-06-28 08:36:56.813704+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 16 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-16-cong-nghe-khoa-hoc-may-tinh-eceeae	<p>Đây là nội dung chi tiết của bài viết mẫu số 16.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PUBLISHED	79e7be5e-899a-4a80-be50-7ac493dce689	2026-06-28 08:36:56.81543+00	2026-06-28 08:36:56.815431+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 17 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-17-cong-nghe-khoa-hoc-may-tinh-e2e067	<p>Đây là nội dung chi tiết của bài viết mẫu số 17.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	ARCHIVED	1da850b8-4bcb-4c39-b887-002fd6c18cd2	2026-06-28 08:36:56.817059+00	2026-06-28 08:36:56.81706+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 18 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-18-cong-nghe-khoa-hoc-may-tinh-c15099	<p>Đây là nội dung chi tiết của bài viết mẫu số 18.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	ARCHIVED	9ec17e40-be70-46a2-8fe0-fca3bed06643	2026-06-28 08:36:56.818711+00	2026-06-28 08:36:56.818712+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 21 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-21-cong-nghe-khoa-hoc-may-tinh-10d633	<p>Đây là nội dung chi tiết của bài viết mẫu số 21.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PUBLISHED	e7a566ea-1f7b-498e-b71d-7ab96d7a6646	2026-06-28 08:36:56.824483+00	2026-06-28 08:36:56.824484+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 23 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-23-cong-nghe-khoa-hoc-may-tinh-1bd964	<p>Đây là nội dung chi tiết của bài viết mẫu số 23.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	ARCHIVED	cb4a214f-704f-41a4-88f0-c7089cae018c	2026-06-28 08:36:56.827543+00	2026-06-28 08:36:56.827545+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 26 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-26-cong-nghe-khoa-hoc-may-tinh-7870e4	<p>Đây là nội dung chi tiết của bài viết mẫu số 26.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	ARCHIVED	d6e00e62-efcd-4472-acc0-ced2e98228e5	2026-06-28 08:36:56.832336+00	2026-06-28 08:36:56.832337+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 27 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-27-cong-nghe-khoa-hoc-may-tinh-14caf9	<p>Đây là nội dung chi tiết của bài viết mẫu số 27.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	9cbe84b1-b9ab-4387-a390-8e7f4056963d	2026-06-28 08:36:56.834004+00	2026-06-28 08:36:56.834005+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 28 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-28-cong-nghe-khoa-hoc-may-tinh-4ce277	<p>Đây là nội dung chi tiết của bài viết mẫu số 28.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	5332a067-429d-44b9-ac16-30dbe64f6ef6	2026-06-28 08:36:56.83566+00	2026-06-28 08:36:56.835661+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 30 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-30-cong-nghe-khoa-hoc-may-tinh-918fbc	<p>Đây là nội dung chi tiết của bài viết mẫu số 30.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PUBLISHED	3a6a8db4-c633-471e-aa5c-addb16f6b66f	2026-06-28 08:36:56.8387+00	2026-06-28 08:36:56.838702+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 32 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-32-cong-nghe-khoa-hoc-may-tinh-7a94de	<p>Đây là nội dung chi tiết của bài viết mẫu số 32.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PUBLISHED	0204a302-738e-4c11-82f6-8382b935c8d7	2026-06-28 08:36:56.84167+00	2026-06-28 08:36:56.841672+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 34 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-34-cong-nghe-khoa-hoc-may-tinh-a0f107	<p>Đây là nội dung chi tiết của bài viết mẫu số 34.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	DRAFT	c7b07587-0d12-4799-aecf-9b64599d1bc6	2026-06-28 08:36:56.845284+00	2026-06-28 08:36:56.845285+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 35 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-35-cong-nghe-khoa-hoc-may-tinh-1d31c1	<p>Đây là nội dung chi tiết của bài viết mẫu số 35.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	DRAFT	30742216-da61-48e8-9b05-fd50dca32cc4	2026-06-28 08:36:56.846866+00	2026-06-28 08:36:56.846871+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 36 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-36-cong-nghe-khoa-hoc-may-tinh-9b0ccd	<p>Đây là nội dung chi tiết của bài viết mẫu số 36.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	ARCHIVED	1d438c93-a543-4f44-b005-d67fdec835e0	2026-06-28 08:36:56.848317+00	2026-06-28 08:36:56.848318+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 37 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-37-cong-nghe-khoa-hoc-may-tinh-b4bd0c	<p>Đây là nội dung chi tiết của bài viết mẫu số 37.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	ARCHIVED	55faf7b2-5c57-4534-9c4b-10c7584d3352	2026-06-28 08:36:56.849742+00	2026-06-28 08:36:56.849743+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 38 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-38-cong-nghe-khoa-hoc-may-tinh-bf200a	<p>Đây là nội dung chi tiết của bài viết mẫu số 38.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	DRAFT	7297cf3b-8340-4e13-925f-d7c10f2f7dd3	2026-06-28 08:36:56.851144+00	2026-06-28 08:36:56.851145+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 39 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-39-cong-nghe-khoa-hoc-may-tinh-d76454	<p>Đây là nội dung chi tiết của bài viết mẫu số 39.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PUBLISHED	a9a51e72-b330-45a5-833b-e470cbb7b061	2026-06-28 08:36:56.852933+00	2026-06-28 08:36:56.852934+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 40 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-40-cong-nghe-khoa-hoc-may-tinh-76bfe0	<p>Đây là nội dung chi tiết của bài viết mẫu số 40.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	8cfba9a1-8272-49a7-afbd-40ef6146888f	2026-06-28 08:36:56.854309+00	2026-06-28 08:36:56.85431+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 42 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-42-cong-nghe-khoa-hoc-may-tinh-626ff9	<p>Đây là nội dung chi tiết của bài viết mẫu số 42.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	8a2e8c0b-c618-4d9c-93a5-b2457597ed27	2026-06-28 08:36:56.857322+00	2026-06-28 08:36:56.857324+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 43 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-43-cong-nghe-khoa-hoc-may-tinh-b1dc8a	<p>Đây là nội dung chi tiết của bài viết mẫu số 43.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	DRAFT	5514a6be-618b-42fa-bf37-170144a56cad	2026-06-28 08:36:56.858771+00	2026-06-28 08:36:56.858772+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 46 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-46-cong-nghe-khoa-hoc-may-tinh-30f8cf	<p>Đây là nội dung chi tiết của bài viết mẫu số 46.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PUBLISHED	169d1692-31e2-4c73-8c39-4d334aac3605	2026-06-28 08:36:56.863375+00	2026-06-28 08:36:56.863376+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 47 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-47-cong-nghe-khoa-hoc-may-tinh-e194c7	<p>Đây là nội dung chi tiết của bài viết mẫu số 47.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	ae393e2f-e4a3-40ce-90e7-8f5f3a6623b5	2026-06-28 08:36:56.865385+00	2026-06-28 08:36:56.865387+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 48 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-48-cong-nghe-khoa-hoc-may-tinh-db941d	<p>Đây là nội dung chi tiết của bài viết mẫu số 48.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	ARCHIVED	0948f7d6-db49-474c-b210-a06f9cebde8a	2026-06-28 08:36:56.86704+00	2026-06-28 08:36:56.867041+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 49 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-49-cong-nghe-khoa-hoc-may-tinh-a7c924	<p>Đây là nội dung chi tiết của bài viết mẫu số 49.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	ARCHIVED	ff81d1f8-d4a1-4f8c-9830-1395422b68c2	2026-06-28 08:36:56.868479+00	2026-06-28 08:36:56.86848+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 50 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-50-cong-nghe-khoa-hoc-may-tinh-92d911	<p>Đây là nội dung chi tiết của bài viết mẫu số 50.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	ec4244ca-41d1-4c10-8e47-60bc0980b619	2026-06-28 08:36:56.870206+00	2026-06-28 08:36:56.870208+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 51 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-51-cong-nghe-khoa-hoc-may-tinh-46a838	<p>Đây là nội dung chi tiết của bài viết mẫu số 51.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	4909e670-9936-44bf-ae5f-e073bee24666	2026-06-28 08:36:56.871614+00	2026-06-28 08:36:56.871615+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 52 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-52-cong-nghe-khoa-hoc-may-tinh-1f694d	<p>Đây là nội dung chi tiết của bài viết mẫu số 52.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	ARCHIVED	034f5094-10c1-471c-8e17-d0b480686f95	2026-06-28 08:36:56.872985+00	2026-06-28 08:36:56.872986+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 53 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-53-cong-nghe-khoa-hoc-may-tinh-e35e80	<p>Đây là nội dung chi tiết của bài viết mẫu số 53.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	ARCHIVED	7490b45e-e0f7-4025-9256-90f0cc2fd8d0	2026-06-28 08:36:56.874435+00	2026-06-28 08:36:56.874437+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 56 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-56-cong-nghe-khoa-hoc-may-tinh-6f0579	<p>Đây là nội dung chi tiết của bài viết mẫu số 56.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	ARCHIVED	1edc21af-5b21-4c64-ae61-bd5dea5ea478	2026-06-28 08:36:56.878458+00	2026-06-28 08:36:56.878459+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 57 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-57-cong-nghe-khoa-hoc-may-tinh-7d195e	<p>Đây là nội dung chi tiết của bài viết mẫu số 57.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	ARCHIVED	a7f2cb0a-ae5c-4190-9443-9bef412c64d4	2026-06-28 08:36:56.879959+00	2026-06-28 08:36:56.879959+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 58 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-58-cong-nghe-khoa-hoc-may-tinh-7fc8e9	<p>Đây là nội dung chi tiết của bài viết mẫu số 58.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	ARCHIVED	a8e61b31-ffb5-45af-b7b1-b14380f9d6a6	2026-06-28 08:36:56.881308+00	2026-06-28 08:36:56.881309+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 60 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-60-cong-nghe-khoa-hoc-may-tinh-92ee37	<p>Đây là nội dung chi tiết của bài viết mẫu số 60.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	DRAFT	12b88af0-f117-4839-8d17-822169ebfca6	2026-06-28 08:36:56.88436+00	2026-06-28 08:36:56.884361+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 61 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-61-cong-nghe-khoa-hoc-may-tinh-2ceadb	<p>Đây là nội dung chi tiết của bài viết mẫu số 61.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	4b2daa35-dcd0-4667-9251-8d7899a87a70	2026-06-28 08:36:56.886805+00	2026-06-28 08:36:56.886806+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 62 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-62-cong-nghe-khoa-hoc-may-tinh-506df0	<p>Đây là nội dung chi tiết của bài viết mẫu số 62.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	ARCHIVED	9d0c81d6-abcf-4d1c-9e24-d18c5b2f95ad	2026-06-28 08:36:56.888178+00	2026-06-28 08:36:56.888179+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 63 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-63-cong-nghe-khoa-hoc-may-tinh-b552c3	<p>Đây là nội dung chi tiết của bài viết mẫu số 63.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	DRAFT	9ce357f7-1e81-424d-81c0-8915655e25ba	2026-06-28 08:36:56.889486+00	2026-06-28 08:36:56.889487+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 66 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-66-cong-nghe-khoa-hoc-may-tinh-9e9f66	<p>Đây là nội dung chi tiết của bài viết mẫu số 66.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	DRAFT	22c0eef1-ef47-49e6-9ce9-9c2a6acaf28d	2026-06-28 08:36:56.893576+00	2026-06-28 08:36:56.893577+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 68 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-68-cong-nghe-khoa-hoc-may-tinh-159ab7	<p>Đây là nội dung chi tiết của bài viết mẫu số 68.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	3de8fe7f-940d-4997-8f0d-2b75d80bfe94	2026-06-28 08:36:56.896463+00	2026-06-28 08:36:56.896464+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 69 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-69-cong-nghe-khoa-hoc-may-tinh-c18bc3	<p>Đây là nội dung chi tiết của bài viết mẫu số 69.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	DRAFT	47cd5d06-68d1-4dae-8e20-8d0d97a99ca5	2026-06-28 08:36:56.897801+00	2026-06-28 08:36:56.897802+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 70 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-70-cong-nghe-khoa-hoc-may-tinh-0f9ecd	<p>Đây là nội dung chi tiết của bài viết mẫu số 70.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PUBLISHED	25c36021-f92a-4ef1-9b6b-23973155de64	2026-06-28 08:36:56.899289+00	2026-06-28 08:36:56.89929+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 71 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-71-cong-nghe-khoa-hoc-may-tinh-280d32	<p>Đây là nội dung chi tiết của bài viết mẫu số 71.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PUBLISHED	199ae547-bd24-486d-8c82-8b80c48692ee	2026-06-28 08:36:56.900553+00	2026-06-28 08:36:56.900554+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 72 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-72-cong-nghe-khoa-hoc-may-tinh-81451a	<p>Đây là nội dung chi tiết của bài viết mẫu số 72.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	3d78a136-93f0-430d-ab01-e369840ee5c9	2026-06-28 08:36:56.901921+00	2026-06-28 08:36:56.901922+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 75 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-75-cong-nghe-khoa-hoc-may-tinh-7a3275	<p>Đây là nội dung chi tiết của bài viết mẫu số 75.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PUBLISHED	d462cbda-0c15-4b72-a486-454ceb40700b	2026-06-28 08:36:56.912014+00	2026-06-28 08:36:56.912016+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 76 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-76-cong-nghe-khoa-hoc-may-tinh-5df0b4	<p>Đây là nội dung chi tiết của bài viết mẫu số 76.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	ARCHIVED	3b19e5f6-75fd-472d-83d3-61a34882865d	2026-06-28 08:36:56.913658+00	2026-06-28 08:36:56.913661+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 77 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-77-cong-nghe-khoa-hoc-may-tinh-78f0f7	<p>Đây là nội dung chi tiết của bài viết mẫu số 77.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PUBLISHED	78551ebc-73ee-4ee2-b555-95d2ffc63815	2026-06-28 08:36:56.915335+00	2026-06-28 08:36:56.915338+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 80 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-80-cong-nghe-khoa-hoc-may-tinh-5ef9ed	<p>Đây là nội dung chi tiết của bài viết mẫu số 80.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PUBLISHED	3c6ab149-3aab-4e09-a8fd-9f4898e37b0c	2026-06-28 08:36:56.920216+00	2026-06-28 08:36:56.920218+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 81 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-81-cong-nghe-khoa-hoc-may-tinh-809dce	<p>Đây là nội dung chi tiết của bài viết mẫu số 81.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	ARCHIVED	96b76e96-32ce-4814-9bce-a60ea6cb525c	2026-06-28 08:36:56.921745+00	2026-06-28 08:36:56.921747+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 82 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-82-cong-nghe-khoa-hoc-may-tinh-610005	<p>Đây là nội dung chi tiết của bài viết mẫu số 82.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	9115777b-36c3-40c0-ad79-fdb7841a7de4	2026-06-28 08:36:56.923244+00	2026-06-28 08:36:56.923246+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 83 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-83-cong-nghe-khoa-hoc-may-tinh-963b04	<p>Đây là nội dung chi tiết của bài viết mẫu số 83.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	DRAFT	a6c765e6-5d46-46b4-8161-b3cdf1ef8001	2026-06-28 08:36:56.924686+00	2026-06-28 08:36:56.924688+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 84 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-84-cong-nghe-khoa-hoc-may-tinh-4566b3	<p>Đây là nội dung chi tiết của bài viết mẫu số 84.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	ARCHIVED	cac2a308-5ad6-4967-b820-572e7bd1140c	2026-06-28 08:36:56.926124+00	2026-06-28 08:36:56.926125+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 85 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-85-cong-nghe-khoa-hoc-may-tinh-521ecb	<p>Đây là nội dung chi tiết của bài viết mẫu số 85.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PUBLISHED	10275283-2d52-4bfe-8ef0-94f8d8416af3	2026-06-28 08:36:56.927677+00	2026-06-28 08:36:56.927679+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 86 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-86-cong-nghe-khoa-hoc-may-tinh-ebf9f3	<p>Đây là nội dung chi tiết của bài viết mẫu số 86.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PUBLISHED	be1bedd6-02e2-4718-881f-38e954a6a038	2026-06-28 08:36:56.929713+00	2026-06-28 08:36:56.929714+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 87 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-87-cong-nghe-khoa-hoc-may-tinh-f26b7f	<p>Đây là nội dung chi tiết của bài viết mẫu số 87.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	7b3b89d1-db5d-4048-9cc2-77032bc59e21	2026-06-28 08:36:56.931238+00	2026-06-28 08:36:56.931239+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 89 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-89-cong-nghe-khoa-hoc-may-tinh-f2a9c7	<p>Đây là nội dung chi tiết của bài viết mẫu số 89.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PUBLISHED	cdc53624-0d2a-4afe-92c2-7e1624c8c93b	2026-06-28 08:36:56.934155+00	2026-06-28 08:36:56.934157+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 90 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-90-cong-nghe-khoa-hoc-may-tinh-e5052e	<p>Đây là nội dung chi tiết của bài viết mẫu số 90.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	c47de751-c33d-4bff-b323-8ad56fc3f64f	2026-06-28 08:36:56.935667+00	2026-06-28 08:36:56.935669+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 93 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-93-cong-nghe-khoa-hoc-may-tinh-2810ff	<p>Đây là nội dung chi tiết của bài viết mẫu số 93.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	bca8699d-b64e-47ec-b30a-b1608b40949f	2026-06-28 08:36:56.940149+00	2026-06-28 08:36:56.940151+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 95 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-95-cong-nghe-khoa-hoc-may-tinh-900bd0	<p>Đây là nội dung chi tiết của bài viết mẫu số 95.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PUBLISHED	01dfc023-2bee-4cf0-8d2f-39b1971c9aaf	2026-06-28 08:36:56.943386+00	2026-06-28 08:36:56.943391+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 96 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-96-cong-nghe-khoa-hoc-may-tinh-a2f624	<p>Đây là nội dung chi tiết của bài viết mẫu số 96.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	DRAFT	0420fb43-222f-4f52-b269-e2d2ceba458b	2026-06-28 08:36:56.944872+00	2026-06-28 08:36:56.944873+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 97 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-97-cong-nghe-khoa-hoc-may-tinh-0e205d	<p>Đây là nội dung chi tiết của bài viết mẫu số 97.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	DRAFT	64af30ed-0fa5-4543-a10b-a446af05ac65	2026-06-28 08:36:56.946471+00	2026-06-28 08:36:56.946473+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 99 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-99-cong-nghe-khoa-hoc-may-tinh-80db91	<p>Đây là nội dung chi tiết của bài viết mẫu số 99.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PUBLISHED	6c29adc8-5a48-4382-a8e7-a72fd90c3832	2026-06-28 08:36:56.949791+00	2026-06-28 08:36:56.949792+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 2 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-2-cong-nghe-khoa-hoc-may-tinh-ec4256	<p>Đây là nội dung chi tiết của bài viết mẫu số 2.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	ecb1670b-9cc2-4f88-ada7-f609d39beb61	2026-06-28 08:36:56.776302+00	2026-06-28 08:36:56.776306+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 3 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-3-cong-nghe-khoa-hoc-may-tinh-6c6f5e	<p>Đây là nội dung chi tiết của bài viết mẫu số 3.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	e6eb602c-dec5-4d2a-a333-675a619d180e	2026-06-28 08:36:56.783647+00	2026-06-28 08:36:56.783653+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 5 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-5-cong-nghe-khoa-hoc-may-tinh-2c747d	<p>Đây là nội dung chi tiết của bài viết mẫu số 5.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	f0e5b7eb-9b63-409d-901c-28eb23a620de	2026-06-28 08:36:56.789739+00	2026-06-28 08:36:56.789741+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 6 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-6-cong-nghe-khoa-hoc-may-tinh-9b1681	<p>Đây là nội dung chi tiết của bài viết mẫu số 6.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	564767bd-8d42-420b-9f0b-93a5f8d0fe8e	2026-06-28 08:36:56.791702+00	2026-06-28 08:36:56.791704+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 13 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-13-cong-nghe-khoa-hoc-may-tinh-418105	<p>Đây là nội dung chi tiết của bài viết mẫu số 13.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	0f0ad3c3-37b2-4d9a-affc-3ce374effcba	2026-06-28 08:36:56.808563+00	2026-06-28 08:36:56.808564+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 14 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-14-cong-nghe-khoa-hoc-may-tinh-c74b17	<p>Đây là nội dung chi tiết của bài viết mẫu số 14.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	efee5679-f81e-4f5f-9836-91752fce12ca	2026-06-28 08:36:56.811448+00	2026-06-28 08:36:56.81145+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 19 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-19-cong-nghe-khoa-hoc-may-tinh-219bc2	<p>Đây là nội dung chi tiết của bài viết mẫu số 19.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	817d9ea9-f03e-44c1-a0a3-feca5e0b803c	2026-06-28 08:36:56.820767+00	2026-06-28 08:36:56.820768+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 20 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-20-cong-nghe-khoa-hoc-may-tinh-a60ed1	<p>Đây là nội dung chi tiết của bài viết mẫu số 20.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	d2ef8177-6bb6-485f-b49d-807539495d46	2026-06-28 08:36:56.822936+00	2026-06-28 08:36:56.822937+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 22 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-22-cong-nghe-khoa-hoc-may-tinh-eb5b8d	<p>Đây là nội dung chi tiết của bài viết mẫu số 22.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	a14d1f0d-fb82-4add-9f3b-4bac51795932	2026-06-28 08:36:56.825951+00	2026-06-28 08:36:56.825952+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 24 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-24-cong-nghe-khoa-hoc-may-tinh-72fa90	<p>Đây là nội dung chi tiết của bài viết mẫu số 24.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	30b3cd43-8fb4-42cc-9b5c-79b8b6df7dfc	2026-06-28 08:36:56.829219+00	2026-06-28 08:36:56.82922+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 25 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-25-cong-nghe-khoa-hoc-may-tinh-f31e63	<p>Đây là nội dung chi tiết của bài viết mẫu số 25.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	34d4d27c-0102-4c89-808a-b30c8d19ef14	2026-06-28 08:36:56.830849+00	2026-06-28 08:36:56.830851+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 29 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-29-cong-nghe-khoa-hoc-may-tinh-c920a4	<p>Đây là nội dung chi tiết của bài viết mẫu số 29.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	b25ecea0-ac12-4b14-afc7-5700d8a4e756	2026-06-28 08:36:56.837199+00	2026-06-28 08:36:56.837201+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 31 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-31-cong-nghe-khoa-hoc-may-tinh-a3dceb	<p>Đây là nội dung chi tiết của bài viết mẫu số 31.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	661de668-7678-4ca6-856e-a71bf4a232bf	2026-06-28 08:36:56.840239+00	2026-06-28 08:36:56.840241+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 33 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-33-cong-nghe-khoa-hoc-may-tinh-7b2252	<p>Đây là nội dung chi tiết của bài viết mẫu số 33.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	87676b19-c0c2-4f2d-b115-e9b300a29c0b	2026-06-28 08:36:56.843786+00	2026-06-28 08:36:56.843788+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 41 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-41-cong-nghe-khoa-hoc-may-tinh-74b8f8	<p>Đây là nội dung chi tiết của bài viết mẫu số 41.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	07ad4631-781a-4d13-8191-b69315659632	2026-06-28 08:36:56.855652+00	2026-06-28 08:36:56.855653+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 44 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-44-cong-nghe-khoa-hoc-may-tinh-c1939d	<p>Đây là nội dung chi tiết của bài viết mẫu số 44.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	5453161a-ecd7-40eb-a529-eecea4c58645	2026-06-28 08:36:56.860299+00	2026-06-28 08:36:56.8603+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 45 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-45-cong-nghe-khoa-hoc-may-tinh-3321e9	<p>Đây là nội dung chi tiết của bài viết mẫu số 45.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	67d444bb-03e9-45c4-949d-0928635c37f3	2026-06-28 08:36:56.861829+00	2026-06-28 08:36:56.86183+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 54 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-54-cong-nghe-khoa-hoc-may-tinh-fe79e2	<p>Đây là nội dung chi tiết của bài viết mẫu số 54.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	e0e96f9f-d2f2-45a1-81cf-b87047c09902	2026-06-28 08:36:56.875792+00	2026-06-28 08:36:56.875793+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 55 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-55-cong-nghe-khoa-hoc-may-tinh-31bbfe	<p>Đây là nội dung chi tiết của bài viết mẫu số 55.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	dcda5cd6-b9ad-4751-95fe-937d98a6d764	2026-06-28 08:36:56.877132+00	2026-06-28 08:36:56.877133+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 59 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-59-cong-nghe-khoa-hoc-may-tinh-2e7299	<p>Đây là nội dung chi tiết của bài viết mẫu số 59.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	10fe3f7a-985b-470f-8b17-19ccaf5ddba9	2026-06-28 08:36:56.882646+00	2026-06-28 08:36:56.882647+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 64 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-64-cong-nghe-khoa-hoc-may-tinh-a8518e	<p>Đây là nội dung chi tiết của bài viết mẫu số 64.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	96ae4a9b-0b66-4f4b-bc2e-7516f5ed5802	2026-06-28 08:36:56.890812+00	2026-06-28 08:36:56.890813+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 65 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-65-cong-nghe-khoa-hoc-may-tinh-0a1646	<p>Đây là nội dung chi tiết của bài viết mẫu số 65.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	d976583c-7b1e-4f7d-8fbb-38fe6f3c9b52	2026-06-28 08:36:56.892188+00	2026-06-28 08:36:56.892189+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 67 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-67-cong-nghe-khoa-hoc-may-tinh-cc1940	<p>Đây là nội dung chi tiết của bài viết mẫu số 67.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	68a923db-27e4-4b56-9b28-f09e39520b32	2026-06-28 08:36:56.895042+00	2026-06-28 08:36:56.895043+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 73 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-73-cong-nghe-khoa-hoc-may-tinh-9e3765	<p>Đây là nội dung chi tiết của bài viết mẫu số 73.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	f2734cfd-5bc1-4872-a1b4-105f7ddb8e64	2026-06-28 08:36:56.903885+00	2026-06-28 08:36:56.903886+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 74 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-74-cong-nghe-khoa-hoc-may-tinh-1fd996	<p>Đây là nội dung chi tiết của bài viết mẫu số 74.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	68d62c7b-ec4c-405a-b577-c1b75cff534e	2026-06-28 08:36:56.909914+00	2026-06-28 08:36:56.909916+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 78 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-78-cong-nghe-khoa-hoc-may-tinh-036ffa	<p>Đây là nội dung chi tiết của bài viết mẫu số 78.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	115ae579-9ff4-44b1-a5cc-7c665ac9e336	2026-06-28 08:36:56.916988+00	2026-06-28 08:36:56.91699+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 79 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-79-cong-nghe-khoa-hoc-may-tinh-21b4a5	<p>Đây là nội dung chi tiết của bài viết mẫu số 79.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	3c32cd9f-118f-4ca4-a327-883fe7fb8f67	2026-06-28 08:36:56.918641+00	2026-06-28 08:36:56.918643+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 88 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-88-cong-nghe-khoa-hoc-may-tinh-4e2e3e	<p>Đây là nội dung chi tiết của bài viết mẫu số 88.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	1d071bcc-cd8c-49fa-b00c-aba9706c6a03	2026-06-28 08:36:56.932759+00	2026-06-28 08:36:56.93276+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 91 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-91-cong-nghe-khoa-hoc-may-tinh-b0e590	<p>Đây là nội dung chi tiết của bài viết mẫu số 91.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	023b775a-78ae-4086-81c2-61fc0caf1be1	2026-06-28 08:36:56.937138+00	2026-06-28 08:36:56.93714+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 92 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-92-cong-nghe-khoa-hoc-may-tinh-792833	<p>Đây là nội dung chi tiết của bài viết mẫu số 92.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	832821d5-66fb-436a-bf1f-fcd4e8a80ae0	2026-06-28 08:36:56.938627+00	2026-06-28 08:36:56.938628+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 94 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-94-cong-nghe-khoa-hoc-may-tinh-a62bc7	<p>Đây là nội dung chi tiết của bài viết mẫu số 94.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	t	PENDING	73a8ad8e-99ed-4689-936d-e20f2812919d	2026-06-28 08:36:56.941913+00	2026-06-28 08:36:56.941914+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a41bf474-295a-4b89-859e-ebd087d81b48	Bài viết mẫu số 98 về Công nghệ và Khoa học Máy tính	bai-viet-mau-so-98-cong-nghe-khoa-hoc-may-tinh-c73760	<p>Đây là nội dung chi tiết của bài viết mẫu số 98.</p><p>Công nghệ thông tin đang thay đổi thế giới từng ngày. Việc nghiên cứu khoa học máy tính đóng vai trò cực kỳ quan trọng trong thời đại số hóa hiện nay.</p>	f	PENDING	b16f43ba-c4c9-41ee-bf9f-d3a2da556167	2026-06-28 08:36:56.947933+00	2026-06-28 08:36:56.947935+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
\N	Article Test Creation	article-test-creation	<p>Content of the article</p>	f	DRAFT	3159c3dc-5db7-4b9c-b014-77a478803ec4	2026-06-28 16:18:59.921267+00	2026-06-28 16:18:59.92127+00	\N	\N	\N	\N	index, follow	\N	Short description	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	0b5c6b7925f52e3bc430ff4cece42c5a3ff33b9f05446b2c0aa01512519805b2	1	\N	\N	\N	vi-VN	1	4	\N	\N	\N	\N	\N	\N
\N	Article Test Creation	article-test-creation-1	<p>Content of the article</p>	f	DRAFT	9b1dd30a-31a8-45d4-b7a0-b8a47ea6ca0e	2026-06-28 16:19:10.486068+00	2026-06-28 16:19:10.48607+00	\N	\N	\N	\N	index, follow	\N	Short description	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	0b5c6b7925f52e3bc430ff4cece42c5a3ff33b9f05446b2c0aa01512519805b2	1	\N	\N	\N	vi-VN	1	4	\N	\N	\N	\N	\N	\N
\N	Article Test Creation	article-test-creation-2	<p>Content of the article has been updated heavily with more words to test the word count logic properly.</p>	f	DRAFT	fa32f0a4-963c-4815-9e59-4299c12ae002	2026-06-28 16:19:48.281815+00	2026-06-28 16:19:48.296509+00	\N	\N	\N	\N	index, follow	\N	Short description	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	7f392a91dbf4494d4a3fea8df4389340fc7e8bd65c3c588d7c5d9567d724a289	2	\N	\N	\N	vi-VN	1	18	\N	\N	\N	\N	\N	\N
\N	Article Test Creation	article-test-creation-3	<p>Content of the article has been updated heavily with more words to test the word count logic properly.</p>	f	DRAFT	8432a964-9ea4-4be7-8f42-c22be3e0b211	2026-06-28 16:19:58.830023+00	2026-06-28 16:19:58.847955+00	\N	\N	\N	\N	index, follow	\N	Short description	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	7f392a91dbf4494d4a3fea8df4389340fc7e8bd65c3c588d7c5d9567d724a289	2	\N	\N	\N	vi-VN	1	18	\N	\N	\N	\N	\N	\N
017ee0d5-c4cd-4a8a-8254-fdc4abdda8ba	My Test Article Workflow	my-test-article-workflow	Full content of the article here	f	DRAFT	f859c304-7130-492e-aaa1-0884de8926fc	2026-06-28 16:29:07.914931+00	2026-06-28 16:29:07.914933+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	26d81ddd9ffd491e6cba0347ce5e0bb6c95617ad6f4eb3852988a34b5491647f	1	\N	\N	\N	vi-VN	1	6	\N	\N	\N	\N	\N	\N
017ee0d5-c4cd-4a8a-8254-fdc4abdda8ba	My Test Article Workflow	my-test-article-workflow-1	Full content of the article here	f	DRAFT	7448c7c3-7d40-433c-8126-6fbdecd03402	2026-06-28 16:30:56.460612+00	2026-06-28 16:30:56.460616+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	26d81ddd9ffd491e6cba0347ce5e0bb6c95617ad6f4eb3852988a34b5491647f	1	\N	\N	\N	vi-VN	1	6	\N	\N	\N	\N	\N	\N
017ee0d5-c4cd-4a8a-8254-fdc4abdda8ba	My Test Article Workflow	my-test-article-workflow-2	Full content of the article here	f	PENDING	15859c70-ddc0-4c66-b282-0d84a9bfa099	2026-06-28 16:32:04.843853+00	2026-06-28 16:32:04.914999+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	26d81ddd9ffd491e6cba0347ce5e0bb6c95617ad6f4eb3852988a34b5491647f	1	\N	\N	\N	vi-VN	1	6	\N	Not enough content	\N	2026-06-29 16:32:04.908845+00	\N	\N
017ee0d5-c4cd-4a8a-8254-fdc4abdda8ba	My Test Article Workflow	my-test-article-workflow-3	Full content of the article here	f	DRAFT	988a8a51-27ac-4d4d-91ec-ee41fb5a74ba	2026-06-28 16:32:27.297839+00	2026-06-28 16:32:27.439413+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	26d81ddd9ffd491e6cba0347ce5e0bb6c95617ad6f4eb3852988a34b5491647f	1	\N	\N	\N	vi-VN	1	6	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	Not enough content	\N	\N	\N	\N
017ee0d5-c4cd-4a8a-8254-fdc4abdda8ba	My Test Article Workflow	my-test-article-workflow-5	Full content of the article here	f	DRAFT	8cf1c754-d6c2-43a9-8778-8869043bc784	2026-06-28 16:38:50.005622+00	2026-06-28 16:38:50.005625+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	26d81ddd9ffd491e6cba0347ce5e0bb6c95617ad6f4eb3852988a34b5491647f	1	\N	\N	\N	vi-VN	1	6	\N	\N	\N	\N	\N	\N
017ee0d5-c4cd-4a8a-8254-fdc4abdda8ba	My Test Article Workflow	my-test-article-workflow-4	Full content of the article here	f	DRAFT	946fe790-22ae-40a3-b08c-9c858c902b0d	2026-06-28 16:34:03.713262+00	2026-06-28 16:34:03.874581+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	26d81ddd9ffd491e6cba0347ce5e0bb6c95617ad6f4eb3852988a34b5491647f	1	\N	\N	\N	vi-VN	1	6	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	Not enough content	\N	\N	\N	\N
017ee0d5-c4cd-4a8a-8254-fdc4abdda8ba	My Test Article Workflow	my-test-article-workflow-6	Full content of the article here	f	DRAFT	96490026-89e6-4fb0-82ca-859f8e02bfc8	2026-06-28 16:39:00.240808+00	2026-06-28 16:39:00.388503+00	\N	\N	\N	\N	index, follow	\N	\N	\N	PUBLIC	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	f	26d81ddd9ffd491e6cba0347ce5e0bb6c95617ad6f4eb3852988a34b5491647f	1	\N	\N	\N	vi-VN	1	6	b6ae329c-6de0-402b-b86a-b0239dcd2ab4	Not enough content	\N	\N	\N	\N
abc2d69d-7b43-4b40-bee7-be00f6cc8bf9	Sự kiện ra mắt AI mới của Google và OpenAI	su-kien-ra-mat-ai-moi-cua-google	Vào hôm nay, Google đã ra mắt phiên bản Gemini Pro mới. Trong khi đó, OpenAI cũng không kém cạnh với GPT-4 Turbo. Hai công ty công nghệ hàng đầu này đang cạnh tranh khốc liệt trong mảng Trí tuệ nhân tạo.	f	DRAFT	5f147b08-75f4-44dc-8d81-f1cdef064cd1	2026-06-28 18:35:30.377168+00	2026-06-28 18:35:30.377171+00	\N	\N	\N	\N	index, follow	\N	Cuộc đua AI giữa Google và OpenAI.	\N	PUBLIC	c62beaf2-5e44-4957-8e88-acd3394f127d	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
0e633b60-83be-4a24-af14-650a048b547b	Sự kiện ra mắt AI mới của Google và OpenAI 7679	su-kien-ra-mat-ai-moi-cua-google-7679	Vào hôm nay, Google đã ra mắt phiên bản Gemini Pro mới. Trong khi đó, OpenAI cũng không kém cạnh với GPT-4 Turbo. Hai công ty công nghệ hàng đầu này đang cạnh tranh khốc liệt trong mảng Trí tuệ nhân tạo.	f	DRAFT	5e282af0-23b5-4956-b52d-9b77e209ab7c	2026-06-28 18:36:07.671633+00	2026-06-28 18:36:07.671637+00	\N	\N	\N	\N	index, follow	\N	Cuộc đua AI giữa Google và OpenAI.	\N	PUBLIC	ce1c9af3-5dc4-4224-9a03-c8c7bed68bc4	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
2e508eeb-84e3-47aa-b9e9-daa7f6f995c5	Sự kiện ra mắt AI mới của Google và OpenAI 2318	su-kien-ra-mat-ai-moi-cua-google-2318	Vào hôm nay, Google đã ra mắt phiên bản Gemini Pro mới. Trong khi đó, OpenAI cũng không kém cạnh với GPT-4 Turbo. Hai công ty công nghệ hàng đầu này đang cạnh tranh khốc liệt trong mảng Trí tuệ nhân tạo.	f	DRAFT	d0213481-2541-4d23-9ed9-badb73c52540	2026-06-28 18:36:24.569007+00	2026-06-28 18:36:24.56901+00	\N	\N	\N	\N	index, follow	\N	Cuộc đua AI giữa Google và OpenAI.	\N	PUBLIC	b5fa1902-5af6-44fa-a4bf-0f03b6aa35c5	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
9dcb0a37-0b39-457c-874a-4114c4dd1ae1	Sự kiện ra mắt AI mới của Google và OpenAI 9484	su-kien-ra-mat-ai-moi-cua-google-9484	Vào hôm nay, Google đã ra mắt phiên bản Gemini Pro mới. Trong khi đó, OpenAI cũng không kém cạnh với GPT-4 Turbo. Hai công ty công nghệ hàng đầu này đang cạnh tranh khốc liệt trong mảng Trí tuệ nhân tạo.	f	DRAFT	9657bbdb-e0a3-4d1c-a228-f76290dc6cad	2026-06-28 18:38:36.376222+00	2026-06-28 18:38:36.376225+00	\N	\N	\N	\N	index, follow	\N	Cuộc đua AI giữa Google và OpenAI.	\N	PUBLIC	1d0bc2c4-1ad5-4b12-a9a2-12bf7830b5f3	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
4a9501cd-d255-4c16-8b35-a718704e6065	Sự kiện ra mắt AI mới của Google và OpenAI 3426	su-kien-ra-mat-ai-moi-cua-google-3426	Vào hôm nay, Google đã ra mắt phiên bản Gemini Pro mới. Trong khi đó, OpenAI cũng không kém cạnh với GPT-4 Turbo. Hai công ty công nghệ hàng đầu này đang cạnh tranh khốc liệt trong mảng Trí tuệ nhân tạo.	f	DRAFT	15f394ae-b05b-4162-80d1-4634742c42cd	2026-06-28 18:39:02.669717+00	2026-06-28 18:39:02.66972+00	\N	\N	\N	\N	index, follow	\N	Cuộc đua AI giữa Google và OpenAI.	\N	PUBLIC	c32d52bf-3d37-4df8-baa1-1be13b6e9a3c	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a51e3abe-ef2f-476a-a4b8-f7737cde812a	Sự kiện ra mắt AI mới của Google và OpenAI 6387	su-kien-ra-mat-ai-moi-cua-google-6387	Vào hôm nay, Google đã ra mắt phiên bản Gemini Pro mới. Trong khi đó, OpenAI cũng không kém cạnh với GPT-4 Turbo. Hai công ty công nghệ hàng đầu này đang cạnh tranh khốc liệt trong mảng Trí tuệ nhân tạo.	f	DRAFT	b09a1799-54a1-435f-b1c8-005f828e85f1	2026-06-28 18:39:54.129607+00	2026-06-28 18:39:54.129613+00	\N	\N	\N	\N	index, follow	\N	Cuộc đua AI giữa Google và OpenAI.	\N	PUBLIC	3a7096f6-b60f-4aa0-8dbc-8429fca93e29	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
f3aa085a-986b-4486-b68c-baa650fc988c	Sự kiện ra mắt AI mới của Google và OpenAI 7474	su-kien-ra-mat-ai-moi-cua-google-7474	Vào hôm nay, Google đã ra mắt phiên bản Gemini Pro mới. Trong khi đó, OpenAI cũng không kém cạnh với GPT-4 Turbo. Hai công ty công nghệ hàng đầu này đang cạnh tranh khốc liệt trong mảng Trí tuệ nhân tạo.	f	DRAFT	44371c70-8a72-4fbf-9926-91b11ca0d5ed	2026-06-28 18:40:55.309539+00	2026-06-28 18:40:55.309541+00	\N	\N	\N	\N	index, follow	\N	Cuộc đua AI giữa Google và OpenAI.	\N	PUBLIC	031cb328-c409-42ba-a35d-94751237f238	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
a951a635-e901-470b-bb3c-2c0964cef5ec	Sự kiện ra mắt AI mới của Google và OpenAI 3905	su-kien-ra-mat-ai-moi-cua-google-3905	Vào hôm nay, Google đã ra mắt phiên bản Gemini Pro mới. Trong khi đó, OpenAI cũng không kém cạnh với GPT-4 Turbo. Hai công ty công nghệ hàng đầu này đang cạnh tranh khốc liệt trong mảng Trí tuệ nhân tạo.	f	DRAFT	5e446833-7cc5-4c35-b282-113d6f9f818d	2026-06-28 18:41:21.931908+00	2026-06-28 18:41:21.931911+00	\N	\N	\N	\N	index, follow	\N	Cuộc đua AI giữa Google và OpenAI.	\N	PUBLIC	0fb9d8ba-dae4-4ad7-8aa6-49cdef5108bd	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
9ee2157e-02df-405b-bcd5-393d709adaee	Sự kiện ra mắt AI mới của Google và OpenAI 2505	su-kien-ra-mat-ai-moi-cua-google-2505	Vào hôm nay, Google đã ra mắt phiên bản Gemini Pro mới. Trong khi đó, OpenAI cũng không kém cạnh với GPT-4 Turbo. Hai công ty công nghệ hàng đầu này đang cạnh tranh khốc liệt trong mảng Trí tuệ nhân tạo.	f	DRAFT	b53b30e9-0061-4e44-b1dd-0e1893a20419	2026-06-28 18:41:50.467747+00	2026-06-28 18:41:50.467751+00	\N	\N	\N	\N	index, follow	\N	Cuộc đua AI giữa Google và OpenAI.	\N	PUBLIC	9842fe66-c68e-4079-b918-21852c4941fa	f	\N	1	\N	\N	\N	vi-VN	0	0	\N	\N	\N	\N	\N	\N
46c5459f-fa75-4ba1-9828-a25b234d79f1	Quy trình tạo bài viết từ A-Z với API	quy-trinh-tao-bai-viet-tu-a-z-voi-api	Nội dung bài viết thử nghiệm luồng A-Z qua FastAPI. AI sẽ sinh SEO và Audio.	f	PUBLISHED	ca6b73d3-1bfb-4f90-8827-9b80b2b9d6dc	2026-06-29 01:14:03.749354+00	2026-06-29 01:14:03.879846+00	\N	\N	\N	\N	index, follow	\N	Test luồng A-Z	\N	PUBLIC	4865719c-133f-4908-a9e3-8219fef46bd9	f	a718ca010ff836c4384f3a7c0b9fb6230db55e8673b58899b808d703bd8c8f18	1	\N	\N	\N	vi-VN	1	16	4865719c-133f-4908-a9e3-8219fef46bd9	\N	2026-06-29 01:14:03.879483+00	\N	\N	\N
a4fff821-cf50-463d-8ec5-f0351b70e2f2	Quy trình tạo bài viết từ A-Z với API	quy-trinh-tao-bai-viet-tu-a-z-voi-api-1	Nội dung bài viết thử nghiệm luồng A-Z qua FastAPI. AI sẽ sinh SEO và Audio.	f	PUBLISHED	de479b8d-3e77-4190-9af6-9e98e0b9b887	2026-06-29 01:14:18.04267+00	2026-06-29 01:14:18.140758+00	\N	\N	\N	\N	index, follow	\N	Test luồng A-Z	\N	PUBLIC	4865719c-133f-4908-a9e3-8219fef46bd9	f	a718ca010ff836c4384f3a7c0b9fb6230db55e8673b58899b808d703bd8c8f18	1	\N	\N	\N	vi-VN	1	16	4865719c-133f-4908-a9e3-8219fef46bd9	\N	2026-06-29 01:14:18.140298+00	\N	\N	\N
cb390bb0-0997-4e98-8df3-be7b1cffede9	Quy trình tạo bài viết từ A-Z với API	quy-trinh-tao-bai-viet-tu-a-z-voi-api-2	Nội dung bài viết thử nghiệm luồng A-Z qua FastAPI. AI sẽ sinh SEO và Audio.	f	DRAFT	47fded5c-e657-4419-adce-c5664272454a	2026-06-29 01:26:59.851317+00	2026-06-29 01:26:59.851324+00	\N	\N	\N	\N	index, follow	\N	Test luồng A-Z	\N	PUBLIC	4865719c-133f-4908-a9e3-8219fef46bd9	f	a718ca010ff836c4384f3a7c0b9fb6230db55e8673b58899b808d703bd8c8f18	1	\N	\N	\N	vi-VN	1	16	\N	\N	\N	\N	\N	null
0d133e8d-bcf4-4711-bcfd-5086323bf507	Quy trình tạo bài viết từ A-Z với API	quy-trinh-tao-bai-viet-tu-a-z-voi-api-3	Nội dung bài viết thử nghiệm luồng A-Z qua FastAPI. AI sẽ sinh SEO và Audio.	f	PUBLISHED	955f4596-23b4-4558-a4b1-720525cf41ab	2026-06-29 01:27:29.252005+00	2026-06-29 01:27:31.435076+00	\N	\N	\N	\N	index, follow	\N	Test luồng A-Z	\N	PUBLIC	4865719c-133f-4908-a9e3-8219fef46bd9	f	a718ca010ff836c4384f3a7c0b9fb6230db55e8673b58899b808d703bd8c8f18	1	\N	\N	\N	vi-VN	1	16	4865719c-133f-4908-a9e3-8219fef46bd9	\N	2026-06-29 01:27:31.434659+00	\N	\N	null
2caf8814-ec56-4ee9-8280-791e0c241220	Quy trình tạo bài viết từ A-Z với API	quy-trinh-tao-bai-viet-tu-a-z-voi-api-4	Nội dung bài viết thử nghiệm luồng A-Z qua FastAPI. AI sẽ sinh SEO và Audio.	f	PUBLISHED	0866e922-44b5-4b46-b208-fee3444b9814	2026-06-29 01:27:49.4171+00	2026-06-29 01:27:51.600482+00	\N	\N	\N	\N	index, follow	\N	Test luồng A-Z	\N	PUBLIC	4865719c-133f-4908-a9e3-8219fef46bd9	f	a718ca010ff836c4384f3a7c0b9fb6230db55e8673b58899b808d703bd8c8f18	1	\N	\N	\N	vi-VN	1	16	4865719c-133f-4908-a9e3-8219fef46bd9	\N	2026-06-29 01:27:51.60011+00	\N	\N	null
4313cfc0-4794-4f31-bcd9-046099968a3e	Quy trình tạo bài viết từ A-Z với API	quy-trinh-tao-bai-viet-tu-a-z-voi-api-5	Nội dung bài viết thử nghiệm luồng A-Z qua FastAPI. AI sẽ sinh SEO và Audio.	f	PUBLISHED	5dbcb7d1-f7d2-433f-a2ee-be43b2633811	2026-06-29 01:28:21.152609+00	2026-06-29 01:28:23.341175+00	\N	\N	\N	\N	index, follow	\N	Test luồng A-Z	\N	PUBLIC	4865719c-133f-4908-a9e3-8219fef46bd9	f	a718ca010ff836c4384f3a7c0b9fb6230db55e8673b58899b808d703bd8c8f18	2	\N	\N	\N	vi-VN	1	16	4865719c-133f-4908-a9e3-8219fef46bd9	\N	2026-06-29 01:28:23.340783+00	\N	\N	["banmai", "minhquang"]
c4cf75cf-b463-420a-afd2-8a079f6b22e3	Quy trình tạo bài viết từ A-Z với API	quy-trinh-tao-bai-viet-tu-a-z-voi-api-6	Nội dung bài viết thử nghiệm luồng A-Z qua FastAPI. AI sẽ sinh SEO và Audio.	f	PUBLISHED	13d993e7-4286-4851-bc6e-c6b5391b093e	2026-06-29 01:30:23.900095+00	2026-06-29 01:30:26.192364+00	\N	\N	\N	\N	index, follow	\N	Test luồng A-Z	\N	PUBLIC	4865719c-133f-4908-a9e3-8219fef46bd9	f	a718ca010ff836c4384f3a7c0b9fb6230db55e8673b58899b808d703bd8c8f18	2	\N	\N	\N	vi-VN	1	16	4865719c-133f-4908-a9e3-8219fef46bd9	\N	2026-06-29 01:30:26.191935+00	\N	\N	["banmai", "minhquang"]
b96b9fa5-ef9e-49d6-89be-d1060f1fe097	Quy trình tạo bài viết từ A-Z với API	quy-trinh-tao-bai-viet-tu-a-z-voi-api-7	Nội dung bài viết thử nghiệm luồng A-Z qua FastAPI. AI sẽ sinh SEO và Audio.	f	PUBLISHED	b06c1052-8210-4ac6-ae6f-5106b51f0ecd	2026-06-29 01:36:19.34359+00	2026-06-29 01:36:21.797329+00	\N	\N	\N	\N	index, follow	\N	Test luồng A-Z	\N	PUBLIC	4865719c-133f-4908-a9e3-8219fef46bd9	f	a718ca010ff836c4384f3a7c0b9fb6230db55e8673b58899b808d703bd8c8f18	2	\N	\N	\N	vi-VN	1	16	4865719c-133f-4908-a9e3-8219fef46bd9	\N	2026-06-29 01:36:21.79614+00	\N	\N	["banmai", "minhquang"]
\.


--
-- Data for Name: tags; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tags (name, slug, description, id, created_at, updated_at) FROM stdin;
\.


--
-- Name: article_relations article_relations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_relations
    ADD CONSTRAINT article_relations_pkey PRIMARY KEY (id);


--
-- Name: article_revision_relations article_revision_relations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_revision_relations
    ADD CONSTRAINT article_revision_relations_pkey PRIMARY KEY (id);


--
-- Name: article_revision_tags article_revision_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_revision_tags
    ADD CONSTRAINT article_revision_tags_pkey PRIMARY KEY (id);


--
-- Name: article_revisions article_revisions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_revisions
    ADD CONSTRAINT article_revisions_pkey PRIMARY KEY (id);


--
-- Name: article_tags article_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_tags
    ADD CONSTRAINT article_tags_pkey PRIMARY KEY (id);


--
-- Name: article_versions article_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_versions
    ADD CONSTRAINT article_versions_pkey PRIMARY KEY (id);


--
-- Name: article_workflow_logs article_workflow_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_workflow_logs
    ADD CONSTRAINT article_workflow_logs_pkey PRIMARY KEY (id);


--
-- Name: articles articles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_pkey PRIMARY KEY (id);


--
-- Name: tags tags_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (id);


--
-- Name: ix_article_relations_source_article_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_relations_source_article_id ON public.article_relations USING btree (source_article_id);


--
-- Name: ix_article_relations_target_article_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_relations_target_article_id ON public.article_relations USING btree (target_article_id);


--
-- Name: ix_article_revision_relations_revision_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_revision_relations_revision_id ON public.article_revision_relations USING btree (revision_id);


--
-- Name: ix_article_revision_relations_target_article_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_revision_relations_target_article_id ON public.article_revision_relations USING btree (target_article_id);


--
-- Name: ix_article_revision_tags_revision_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_revision_tags_revision_id ON public.article_revision_tags USING btree (revision_id);


--
-- Name: ix_article_revision_tags_tag_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_revision_tags_tag_id ON public.article_revision_tags USING btree (tag_id);


--
-- Name: ix_article_revisions_article_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_revisions_article_id ON public.article_revisions USING btree (article_id);


--
-- Name: ix_article_revisions_author_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_revisions_author_id ON public.article_revisions USING btree (author_id);


--
-- Name: ix_article_revisions_category_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_revisions_category_id ON public.article_revisions USING btree (category_id);


--
-- Name: ix_article_revisions_slug; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_revisions_slug ON public.article_revisions USING btree (slug);


--
-- Name: ix_article_revisions_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_revisions_status ON public.article_revisions USING btree (status);


--
-- Name: ix_article_tags_article_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_tags_article_id ON public.article_tags USING btree (article_id);


--
-- Name: ix_article_tags_tag_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_tags_tag_id ON public.article_tags USING btree (tag_id);


--
-- Name: ix_article_versions_article_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_versions_article_id ON public.article_versions USING btree (article_id);


--
-- Name: ix_article_workflow_logs_action; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_workflow_logs_action ON public.article_workflow_logs USING btree (action);


--
-- Name: ix_article_workflow_logs_action_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_workflow_logs_action_by ON public.article_workflow_logs USING btree (action_by);


--
-- Name: ix_article_workflow_logs_article_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_article_workflow_logs_article_id ON public.article_workflow_logs USING btree (article_id);


--
-- Name: ix_articles_author_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_articles_author_id ON public.articles USING btree (author_id);


--
-- Name: ix_articles_category_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_articles_category_id ON public.articles USING btree (category_id);


--
-- Name: ix_articles_slug; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_articles_slug ON public.articles USING btree (slug);


--
-- Name: ix_articles_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_articles_status ON public.articles USING btree (status);


--
-- Name: ix_articles_translation_group_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_articles_translation_group_id ON public.articles USING btree (translation_group_id);


--
-- Name: ix_tags_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_tags_name ON public.tags USING btree (name);


--
-- Name: ix_tags_slug; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_tags_slug ON public.tags USING btree (slug);


--
-- Name: article_relations article_relations_source_article_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_relations
    ADD CONSTRAINT article_relations_source_article_id_fkey FOREIGN KEY (source_article_id) REFERENCES public.articles(id) ON DELETE CASCADE;


--
-- Name: article_relations article_relations_target_article_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_relations
    ADD CONSTRAINT article_relations_target_article_id_fkey FOREIGN KEY (target_article_id) REFERENCES public.articles(id) ON DELETE CASCADE;


--
-- Name: article_revision_relations article_revision_relations_revision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_revision_relations
    ADD CONSTRAINT article_revision_relations_revision_id_fkey FOREIGN KEY (revision_id) REFERENCES public.article_revisions(id) ON DELETE CASCADE;


--
-- Name: article_revision_relations article_revision_relations_target_article_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_revision_relations
    ADD CONSTRAINT article_revision_relations_target_article_id_fkey FOREIGN KEY (target_article_id) REFERENCES public.articles(id) ON DELETE CASCADE;


--
-- Name: article_revision_tags article_revision_tags_revision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_revision_tags
    ADD CONSTRAINT article_revision_tags_revision_id_fkey FOREIGN KEY (revision_id) REFERENCES public.article_revisions(id) ON DELETE CASCADE;


--
-- Name: article_revision_tags article_revision_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_revision_tags
    ADD CONSTRAINT article_revision_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: article_revisions article_revisions_article_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_revisions
    ADD CONSTRAINT article_revisions_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.articles(id) ON DELETE CASCADE;


--
-- Name: article_revisions article_revisions_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_revisions
    ADD CONSTRAINT article_revisions_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: article_revisions article_revisions_banner_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_revisions
    ADD CONSTRAINT article_revisions_banner_image_id_fkey FOREIGN KEY (banner_image_id) REFERENCES public.media_items(id) ON DELETE SET NULL;


--
-- Name: article_revisions article_revisions_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_revisions
    ADD CONSTRAINT article_revisions_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE SET NULL;


--
-- Name: article_revisions article_revisions_locked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_revisions
    ADD CONSTRAINT article_revisions_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: article_revisions article_revisions_seo_og_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_revisions
    ADD CONSTRAINT article_revisions_seo_og_image_id_fkey FOREIGN KEY (seo_og_image_id) REFERENCES public.media_items(id) ON DELETE SET NULL;


--
-- Name: article_tags article_tags_article_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_tags
    ADD CONSTRAINT article_tags_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.articles(id) ON DELETE CASCADE;


--
-- Name: article_tags article_tags_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_tags
    ADD CONSTRAINT article_tags_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: article_versions article_versions_article_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_versions
    ADD CONSTRAINT article_versions_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.articles(id) ON DELETE CASCADE;


--
-- Name: article_versions article_versions_published_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_versions
    ADD CONSTRAINT article_versions_published_by_fkey FOREIGN KEY (published_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: article_workflow_logs article_workflow_logs_action_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_workflow_logs
    ADD CONSTRAINT article_workflow_logs_action_by_fkey FOREIGN KEY (action_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: article_workflow_logs article_workflow_logs_article_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.article_workflow_logs
    ADD CONSTRAINT article_workflow_logs_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.articles(id) ON DELETE CASCADE;


--
-- Name: articles articles_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: articles articles_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id) ON DELETE RESTRICT;


--
-- Name: articles articles_banner_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_banner_image_id_fkey FOREIGN KEY (banner_image_id) REFERENCES public.media_items(id) ON DELETE SET NULL;


--
-- Name: articles articles_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id) ON DELETE SET NULL;


--
-- Name: articles articles_locked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_locked_by_fkey FOREIGN KEY (locked_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: articles articles_seo_og_image_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.articles
    ADD CONSTRAINT articles_seo_og_image_id_fkey FOREIGN KEY (seo_og_image_id) REFERENCES public.media_items(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict JPXuWigmS0FyKV3vN6bLtnbvNaGcdoF6wf07Vb7aeiOQfyTh1CbHzpoHKxahZOm

