% Smart Study Planner – Prolog AI Rules
% -----------------------------------

% Difficulty levels: low, medium, high
% Priority levels: low, medium, high
% DaysLeft: number of days remaining until exam

% Base study hours based on difficulty
difficulty_hours(low, 2).
difficulty_hours(medium, 4).
difficulty_hours(high, 6).

% Bonus hours based on priority
priority_bonus(low, 0).
priority_bonus(medium, 1).
priority_bonus(high, 2).

% Urgency bonus based on exam proximity
urgency_bonus(DaysLeft, 2) :- DaysLeft =< 7.
urgency_bonus(DaysLeft, 1) :- DaysLeft > 7, DaysLeft =< 14.
urgency_bonus(DaysLeft, 0) :- DaysLeft > 14.

% Final rule: calculate total study hours
calculate_hours(Difficulty, Priority, DaysLeft, Hours) :-
    difficulty_hours(Difficulty, Base),
    priority_bonus(Priority, PBonus),
    urgency_bonus(DaysLeft, UBonus),
    Hours is Base + PBonus + UBonus.
