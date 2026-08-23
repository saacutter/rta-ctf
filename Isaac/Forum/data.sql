INSERT INTO Users(username, email, password) 
VALUES
('alice', 'alice@example.com', 'password'),
('bob', 'bob@example.com', 'password'),
('carol', 'carol@example.com', 'password'),
('dave', 'dave@example.com', 'password'),
('erin', 'erin@example.com', 'password');

INSERT INTO Posts(title, body, author, created_at) 
VALUES
('Reverse Engineering #1', 'Providing the reverse engineering binary (also provides a hint for XSS) <a href="/RE/re" download="re">Binary</a>', 1, '2026-08-10'),
('Reverse Engineering #2', 'Providing a hint for how to use setuid programs once the user is on the webserver', 2, '2026-08-10'),
('Admin Post', 'Provides a hint that the admin user is always active and monitoring new posts on the homepage (every 30 seconds)', 3, '2020-05-29');

INSERT INTO Comments(post, author, body, created_at) 
VALUES
(1, 2, 'Hint #1', '2026-08-12'),
(1, 4, 'Hint #2', '2026-08-12'),
(2, 1, 'Hint #1', '2026-08-12');