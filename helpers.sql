-- スレッド一覧 (最新更新順)
.headers on
.mode column
SELECT id, title,
       datetime(update_time,'unixepoch') AS updated,
       (SELECT COUNT(*) FROM messages m
        JOIN conversation_nodes n ON m.msg_id=n.node_id
        WHERE n.conv_id = c.id) AS msgs
FROM conversations c
ORDER BY update_time DESC
LIMIT 10;

-- 1 スレッドのタイムライン (role + テキスト)
-- :conv は対話モードで `.param set conv 1`
WITH RECURSIVE t(node_id, depth) AS (
  SELECT node_id, 0 FROM conversation_nodes
   WHERE conv_id = :conv AND parent_id IS NULL
  UNION ALL
  SELECT n.node_id, depth+1
  FROM conversation_nodes n JOIN t ON n.parent_id = t.node_id
)
SELECT printf('%.*s› ', depth, '        ')  -- インデント
       role, part_text
FROM t
JOIN messages        USING (node_id)
JOIN message_parts   USING (msg_id)
ORDER BY create_time;

