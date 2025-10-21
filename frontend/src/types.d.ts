interface User {
  id: number;
  name: string;
  nickname: string;
  discord: string;
}

type Participant = {
  id: number;
  name: string;
  users: User[];
};

type Match = {
  id: number;
  tournament_id: number;
  match_date: string | null;
  participants: (MatchParticipantSchema | null)[];
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
  status: 'open' | 'running' | 'finished' | 'closed';
};

type LeaderboardEntry = {
  user_id: number;
  name: string;
  nickname: string;
  total_points: number;
  single_wins: number;
  double_wins: number;
  single_manches: number;
  double_manches: number;
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
  participants: MatchParticipantSchema[];
  matches: MatchDetailSchema[];
};

type MatchDetailSchema = {
  id: number;
  participants: MatchParticipantSchema[];
  status: string;
  pool_id: number | null;
  round: number | null;
};

type MatchParticipantSchema = {
  participant_id: number;
  name: string;
  users: User[];
  score: number | null;
};

type LSEFCategory = {
  category: string;
  entries: LSEFEntry[];
}

type CMERCategory = {
  category: string;
  entries: CMEREntry[];
}

type LSEFEntry = {
  joueur: string;
  ol1: string;
  ol2: string;
  ol3: string;
  cl: string;
  ol4: string;
  e1: string;
  e2: string;
  empty1: string;
  master: string;
  pts_com: string;
  empty2: string;
  pts: string;
  clt: string;
}

type CMEREntry = {
  joueur: string;
  oc1: string;
  cc: string;
  oc2: string;
  oc3: string;
  oc4: string;
  oc5: string;
  e1: string;
  e2: string;
  pts: string;
  clt: string;
}

type OfficialEvent = {
  id: number;
  name: string;
  description: string | null;
  organiser: string | null;
  place: string | null;
  date: string;
}

type InscriptionResponse = {
  id: number
  date: string
  name: string
  surname: string
  club: string
  category_simple: string | null
  category_double: string | null
  doublette: number | null
}