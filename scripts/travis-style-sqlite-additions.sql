-- TravisVideoFinder style schema additions
-- Adds style-level columns derived from per-video AI analyses so videos can be
-- filtered and ranked by stylistic attributes (hook, structure, CTA, etc.)
-- All JSON-typed fields are stored as TEXT (SQLite has no native JSON column).
-- Boolean-like fields are stored as INTEGER (0 / 1).

-- Refined taxonomy of the video format. Examples in corpus:
-- travis_solo_tutorial, travis_solo_advice, student_case_study, travis_solo_vlog,
-- vs_comparison, listicle_top_n, interview, ad_promo, news_or_reaction,
-- product_review, deep_dive, live_event_or_qa, other.
ALTER TABLE videos ADD COLUMN refined_video_type TEXT;

-- Who the video is aimed at. Examples:
-- beginner_aspiring, intermediate_seller, advanced_seller,
-- course_lead_aspirational, broad_general.
ALTER TABLE videos ADD COLUMN audience_intent TEXT;

-- Opening hook archetype. Examples:
-- tutorial_promise, money_promise, result_reveal, list_promise,
-- controversial_claim, problem_statement, question, direct_address,
-- scene_set, behind_the_scenes_intro, story, mystery, before_after_tease, other.
ALTER TABLE videos ADD COLUMN hook_type TEXT;

-- How the body of the video is organized. Examples:
-- step_by_step_tutorial, numbered_list, case_study_revealed, problem_solution,
-- vs_comparison, story_arc, mixed_freeform, interview_qa, vlog_chronological,
-- before_after, other.
ALTER TABLE videos ADD COLUMN body_structure TEXT;

-- Call to action archetype. Examples:
-- multiple_layered, course_link, free_resource, subscribe_only,
-- comment_engagement, book_call, none, other.
ALTER TABLE videos ADD COLUMN cta_type TEXT;

-- How the video ends. Examples:
-- course_link_pitch, free_resource_pitch, subscribe_outro,
-- enjoy_the_journey_signoff, abrupt, story_close.
ALTER TABLE videos ADD COLUMN ending_move TEXT;

-- Overall tonal frame. Examples:
-- warm_mentor, technical_walkthrough, story_first, direct_no_BS,
-- casual_vlog, energetic_pitch, controversial_take, other.
ALTER TABLE videos ADD COLUMN framing_style TEXT;

-- Integer 1 to 10 score of how strongly the video expresses Travis's signature style.
ALTER TABLE videos ADD COLUMN style_strength_score INTEGER;

-- JSON array (stored as TEXT) of recurring verbal tics or phrases used in the video.
ALTER TABLE videos ADD COLUMN voice_tics_json TEXT;

-- JSON array (stored as TEXT) of signature rhetorical or framing moves Travis uses.
ALTER TABLE videos ADD COLUMN signature_moves_json TEXT;

-- JSON array (stored as TEXT) of refined topic tags for the video.
ALTER TABLE videos ADD COLUMN topic_tags_refined_json TEXT;

-- 0 / 1 flag: whether Travis shares a personal anecdote or story.
ALTER TABLE videos ADD COLUMN uses_personal_anecdote INTEGER;

-- 0 / 1 flag: whether specific dollar figures or revenue numbers are mentioned.
ALTER TABLE videos ADD COLUMN money_figures_mentioned INTEGER;

-- 0 / 1 flag: whether the video references Travis's other videos or content.
ALTER TABLE videos ADD COLUMN self_references_other_videos INTEGER;

-- Verbatim text of the opening hook (first beat of the video).
ALTER TABLE videos ADD COLUMN hook_text_verbatim TEXT;

-- Verbatim text of the primary call to action.
ALTER TABLE videos ADD COLUMN cta_text_verbatim TEXT;

-- Indexes to support style-faceted browsing and ranking.
CREATE INDEX IF NOT EXISTS idx_videos_refined_video_type ON videos(refined_video_type);
CREATE INDEX IF NOT EXISTS idx_videos_audience_intent     ON videos(audience_intent);
CREATE INDEX IF NOT EXISTS idx_videos_hook_type           ON videos(hook_type);
CREATE INDEX IF NOT EXISTS idx_videos_style_strength      ON videos(style_strength_score);

-- ---------------------------------------------------------------------------
-- Python helper script to backfill the new columns from /tmp/all_analyses.jsonl
-- ---------------------------------------------------------------------------
--
-- ```python
-- import json
-- import sqlite3
--
-- JSONL_PATH = "/tmp/all_analyses.jsonl"
-- DB_PATH = "/Users/connorbyers/Documents/TravisVideoFinder/indexer/data/index.sqlite"
--
-- UPDATE_SQL = """
--     UPDATE videos
--        SET refined_video_type           = ?,
--            audience_intent              = ?,
--            hook_type                    = ?,
--            body_structure               = ?,
--            cta_type                     = ?,
--            ending_move                  = ?,
--            framing_style                = ?,
--            style_strength_score         = ?,
--            voice_tics_json              = ?,
--            signature_moves_json         = ?,
--            topic_tags_refined_json      = ?,
--            uses_personal_anecdote       = ?,
--            money_figures_mentioned      = ?,
--            self_references_other_videos = ?,
--            hook_text_verbatim           = ?,
--            cta_text_verbatim            = ?
--      WHERE video_id = ?
-- """
--
-- def to_int_bool(v):
--     if v is None:
--         return None
--     return 1 if v else 0
--
-- def to_json_text(v):
--     if v is None:
--         return None
--     return json.dumps(v, ensure_ascii=False)
--
-- def main():
--     conn = sqlite3.connect(DB_PATH)
--     cur = conn.cursor()
--     updated = 0
--     with open(JSONL_PATH, "r", encoding="utf-8") as fh:
--         for line in fh:
--             line = line.strip()
--             if not line:
--                 continue
--             row = json.loads(line)
--             params = (
--                 row.get("refined_video_type"),
--                 row.get("audience_intent"),
--                 row.get("hook_type"),
--                 row.get("body_structure"),
--                 row.get("cta_type"),
--                 row.get("ending_move"),
--                 row.get("framing_style"),
--                 row.get("style_strength_score"),
--                 to_json_text(row.get("voice_tics")),
--                 to_json_text(row.get("signature_moves")),
--                 to_json_text(row.get("topic_tags")),
--                 to_int_bool(row.get("uses_personal_anecdote")),
--                 to_int_bool(row.get("money_figures_mentioned")),
--                 to_int_bool(row.get("self_references_other_videos")),
--                 row.get("hook_text_verbatim"),
--                 row.get("cta_text_verbatim"),
--                 row.get("video_id"),
--             )
--             cur.execute(UPDATE_SQL, params)
--             updated += cur.rowcount if cur.rowcount > 0 else 1
--     conn.commit()
--     conn.close()
--     print(f"updated {updated} rows")
--
-- if __name__ == "__main__":
--     main()
-- ```
