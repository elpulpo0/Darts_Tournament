/**
 * Crée des pools équilibrées, corrige en forçant au moins 1 pool et jamais plus de pools que de participants.
 */
export function createPools(participants: Participant[], requestedNumPools: number): Pool[] {
    const numPools = Math.max(1, Math.min(requestedNumPools, participants.length));
    console.warn("[createPools] création des pools:", numPools, "participants:", participants.map(p => `${p.id} - ${p.name}`));
    const pools: Pool[] = [];
    for (let i = 0; i < numPools; i++) {
        pools.push({ id: i + 1, name: `Poule ${String.fromCharCode(65 + i)}`, participants: [], matches: [] });
    }
    const shuffledParticipants = [...participants].sort(() => Math.random() - 0.5);
    let idx = 0;
    for (const participant of shuffledParticipants) {
        pools[idx % numPools].participants.push(participant);
        idx++;
    }
    // Logs de répartition
    for (const pool of pools) {
        console.warn(`POOL ${pool.id} participants:`, pool.participants.map(p => `${p.id} - ${p.name}`));
    }
    pools.forEach(pool => {
        pool.matches = generatePoolMatches(pool.participants, pool.id);
    });
    for (const pool of pools) {
        console.warn(
            `APRES MATCHES > POOL ${pool.id}:`,
            pool.matches.map(m => m.participants.map(p => p?.name).join(" vs "))
        );
    }
    return pools;
}

export function generatePoolMatches(participants: Participant[], pool_id: number): Match[] {
    const matches: Match[] = [];
    let matchId = 1;
    for (let i = 0; i < participants.length; i++) {
        for (let j = i + 1; j < participants.length; j++) {
            const p1 = participantToMatchParticipant(participants[i]);
            const p2 = participantToMatchParticipant(participants[j]);
            if (p1 && p2) {
                matches.push({
                    id: matchId++,
                    tournament_id: 0,
                    match_date: null,
                    participants: [p1, p2],
                    status: 'pending',
                    round: 1,
                    pool_id
                });
            }
        }
    }
    return matches;
}

export function generateEliminationMatches(participants: Participant[]): Match[] {
    if (participants.length < 2) {
        throw new Error("Au moins 2 participants sont requis pour un tournoi à élimination");
    }
    if (participants.length % 2 !== 0) {
        throw new Error("Nombre impair de participants non supporté en mode élimination sans bye");
    }
    const matches: Match[] = [];
    const shuffledParticipants = [...participants].sort(() => Math.random() - 0.5);
    for (let i = 0; i < shuffledParticipants.length; i += 2) {
        const p1 = participantToMatchParticipant(shuffledParticipants[i]);
        const p2 = participantToMatchParticipant(shuffledParticipants[i + 1]);
        if (p1 && p2) {
            matches.push({
                id: 0,
                tournament_id: 0,
                match_date: null,
                participants: [p1, p2],
                status: 'pending',
                round: 1,
                pool_id: undefined
            });
        }
    }
    return matches;
}

/**
 * Convertit un participant en MatchParticipant
 */
export function participantToMatchParticipant(participant: Participant): MatchParticipant | null {
    if (!participant) return null;
    return {
        participant_id: participant.id,
        name: participant.type === 'team' ? `${participant.name} (${participant.users.map(u => u.name).join(' & ')})` : participant.name,
        score: null
    };
}

/**
 * Calcule le classement d'une poule en fonction des victoires, manches, et matchs directs
 */
export function computePoolRanking(poolMatches: Match[]): TournamentLeaderboardEntry[] {
    const stats: { [participantId: number]: { participant_id: number, name: string, wins: number, total_manches: number } } = {};
    for (const match of poolMatches) {
        const participants = match.participants;
        if (participants.length !== 2) continue;
        const p0 = participants[0];
        const p1 = participants[1];
        if (!p0 || !p1) continue;
        if (!stats[p0.participant_id]) stats[p0.participant_id] = { participant_id: p0.participant_id, name: p0.name, wins: 0, total_manches: 0 };
        if (!stats[p1.participant_id]) stats[p1.participant_id] = { participant_id: p1.participant_id, name: p1.name, wins: 0, total_manches: 0 };
        if (p0.score != null) stats[p0.participant_id].total_manches += p0.score;
        if (p1.score != null) stats[p1.participant_id].total_manches += p1.score;
        if (p0.score != null && p1.score != null) {
            if (p0.score > p1.score) stats[p0.participant_id].wins++;
            else if (p1.score > p1.score) stats[p1.participant_id].wins++;
        }
    }

    const getDirectMatchWinner = (participantId1: number, participantId2: number): number | null => {
        for (const match of poolMatches) {
            const participants = match.participants;
            if (participants.length === 2 && participants[0] && participants[1]) {
                const p0 = participants[0];
                const p1 = participants[1];
                if (
                    (p0.participant_id === participantId1 && p1.participant_id === participantId2) ||
                    (p0.participant_id === participantId2 && p1.participant_id === participantId1)
                ) {
                    if (p0.score != null && p1.score != null) {
                        if (p0.score > p1.score) return p0.participant_id;
                        if (p1.score > p0.score) return p1.participant_id;
                    }
                }
            }
        }
        return null;
    };

    return Object.values(stats).sort((a, b) => {
        if (b.wins !== a.wins) return b.wins - a.wins;
        if (b.total_manches !== a.total_manches) return b.total_manches - a.total_manches;
        const directWinnerId = getDirectMatchWinner(a.participant_id, b.participant_id);
        if (directWinnerId === a.participant_id) return -1;
        if (directWinnerId === b.participant_id) return 1;
        return a.participant_id - b.participant_id;
    });
}

/**
 * Trouve le gagnant d'un match à 2 participants
 */
export function getMatchWinner(match: Match): MatchParticipant | null {
    if (!match.participants || match.participants.length !== 2) return null;
    const [p1, p2] = match.participants;
    if (!p1 || !p2) return null;
    if (p1.score == null || p2.score == null) return null;
    if (p1.score > p2.score) return p1;
    if (p2.score > p1.score) return p2;
    return null;
}

/**
 * Génère la finale à partir des gagnants des demi-finales
 */
export function generateFinalFromSemiWinners(semi1: Match, semi2: Match): Match[] {
    const w1 = getMatchWinner(semi1);
    const w2 = getMatchWinner(semi2);
    if (w1 && w2) {
        return [{
            id: 0,
            tournament_id: 0,
            match_date: null,
            participants: [
                { participant_id: w1.participant_id, name: w1.name, score: null },
                { participant_id: w2.participant_id, name: w2.name, score: null }
            ],
            status: 'pending',
            round: 3,
            pool_id: undefined
        }];
    }
    return [];
}