type User = { id: number; name: string };

type Participant = {
  id: number;
  type: 'player' | 'team';
  name: string;
  users: User[];
};

type MatchParticipant = { participant_id: number; name: string; score: number | null };

type Match = {
  id: number;
  tournament_id: number;
  match_date: string | null;
  participants: (MatchParticipant | null)[];
  status: 'pending' | 'completed' | 'cancelled';
  round?: number;
  pool_id?: number;
};

type Pool = {
  id: number;
  name: string;
  participants: Participant[];
  matches: Match[];
};

type Tournament = {
  id: number;
  name: string;
  description: string | null;
  start_date: string;
  is_active: boolean;
  type: 'pool' | 'elimination' | null;
  mode: 'single' | 'double' | null;
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
  participant_id: number;
  name: string;
  wins: number;
  total_manches: number;
}

type TournamentStructure = {
  type: 'elimination' | 'pool';
  matches: Match[];
};

type TournamentFullDetailSchema = {
  id: number;
  name: string;
  type: string | null;
  mode: string | null;
  status: string;
  pools: PoolDetailSchema[];
  final_matches: MatchDetailSchema[];
};

type PoolDetailSchema = {
  id: number;
  name: string | null;
  participants: ParticipantBasicSchema[];
  matches: MatchDetailSchema[];
};

type ParticipantBasicSchema = {
  id: number;
  name: string;
};

type MatchDetailSchema = {
  id: number;
  participants: MatchParticipantSchema[];
  status: string;
  pool_id: number | null;
  round: number | null;
};

type MatchParticipantSchema = {
  id: number;
  name: string;
  score: number | null;
};