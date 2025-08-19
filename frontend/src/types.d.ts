type Player = { id: number; name: string };

type MatchPlayer = { user_id: number; name: string; score: number | null };

type Match = {
  id: number;
  tournament_id: number;
  match_date: string | null;
  players: (MatchPlayer | null)[];
  status: 'pending' | 'completed' | 'cancelled';
  round?: number;
  pool_id?: number;
};

type Pool = {
  id: number;
  name: string;
  players: Player[];
  matches: Match[];
};

type Tournament = {
  id: number;
  name: string;
  description: string | null;
  start_date: string;
  is_active: boolean;
  type: 'pool' | 'elimination';
  status: 'open' | 'running' | 'closed';
};

type LeaderboardEntry = {
  user_id: number;
  name: string;
  total_points: number;
  wins: number;
  total_manches: number;
};

type TournamentLeaderboardEntry = {
  user_id: number;
  name: string;
  wins: number;
  total_manches: number;
}

type TournamentStructure = {
  type: 'elimination' | 'pool';
  matches: Match[];
};