/**
 * Crée des pools équilibrées, corrige en forçant au moins 1 pool et jamais plus de pools que de joueurs.
 */
export function createPools(players: Player[], requestedNumPools: number): Pool[] {
    const numPools = Math.max(1, Math.min(requestedNumPools, players.length));
    console.warn("[createPools] création des pools:", numPools, "joueurs:", players.map(p => `${p.id} - ${p.name}`));
    const pools: Pool[] = [];
    for (let i = 0; i < numPools; i++) {
        pools.push({ id: i + 1, name: `Poule ${String.fromCharCode(65 + i)}`, players: [], matches: [] });
    }
    let idx = 0;
    for (const player of players) {
        pools[idx % numPools].players.push(player);
        idx++;
    }
    // Logs de répartition
    for (const pool of pools) {
        console.warn(`POOL ${pool.id} joueurs:`, pool.players.map(p => `${p.id} - ${p.name}`));
    }
    pools.forEach(pool => {
        pool.matches = generatePoolMatches(pool.players, pool.id);
    });
    for (const pool of pools) {
        console.warn(
            `APRES MATCHES > POOL ${pool.id}:`,
            pool.matches.map(m => m.players.map(p => p?.name).join(" vs "))
        );
    }
    return pools;
}

export function generatePoolMatches(players: Player[], pool_id: number): Match[] {
    const matches: Match[] = [];
    let matchId = 1;
    for (let i = 0; i < players.length; i++) {
        for (let j = i + 1; j < players.length; j++) {
            const p1 = playerToMatchPlayer(players[i]);
            const p2 = playerToMatchPlayer(players[j]);
            if (p1 && p2) {
                matches.push({
                    id: matchId++,
                    tournament_id: 0,
                    match_date: null,
                    players: [p1, p2],
                    status: 'pending',
                    round: 1,
                    pool_id
                });
            }
        }
    }
    return matches;
}

export function generateEliminationMatches(players: Player[]): Match[] {
    if (players.length < 2) {
        throw new Error("Au moins 2 joueurs sont requis pour un tournoi à élimination");
    }
    if (players.length % 2 !== 0) {
        throw new Error("Nombre impair de joueurs non supporté en mode élimination sans bye");
    }
    const matches: Match[] = [];
    // Mélanger les joueurs pour des appariements aléatoires
    const shuffledPlayers = [...players].sort(() => Math.random() - 0.5);
    // Créer les matchs du Round 1
    for (let i = 0; i < shuffledPlayers.length; i += 2) {
        const p1 = playerToMatchPlayer(shuffledPlayers[i]);
        const p2 = playerToMatchPlayer(shuffledPlayers[i + 1]);
        if (p1 && p2) {
            matches.push({
                id: 0, // ID attribué par le backend
                tournament_id: 0, // Défini par createAndPersistMatch
                match_date: null,
                players: [p1, p2],
                status: 'pending',
                round: 1,
                pool_id: undefined,
            });
        }
    }
    return matches;
}

function playerToMatchPlayer(p: Player | null): MatchPlayer | null {
    if (!p) return null;
    return { user_id: p.id, name: p.name, score: null };
}

/**
 * Calcule le classement des joueurs d'une poule sur la base des scores/victoires.
 */
export function computePoolRanking(
    poolMatches: Match[]
): { user_id: number; name: string; points: number; wins: number }[] {
    const stats: Record<number, { user_id: number; name: string; points: number; wins: number }> = {};

    // Calculer les stats (victoires et manches)
    for (const match of poolMatches) {
        for (const p of match.players) {
            if (!p) continue;
            if (!stats[p.user_id]) stats[p.user_id] = { user_id: p.user_id, name: p.name, points: 0, wins: 0 };
            if (typeof p.score === 'number') stats[p.user_id].points += p.score ?? 0;
        }
        const [p0, p1] = match.players;
        if (p0 && p1 && p0.score != null && p1.score != null) {
            if (p0.score > p1.score) stats[p0.user_id].wins++;
            else if (p1.score > p0.score) stats[p1.user_id].wins++;
        }
    }

    // Fonction pour vérifier le match direct
    const getDirectMatchWinner = (userId1: number, userId2: number): number | null => {
        for (const match of poolMatches) {
            const players = match.players;
            if (players.length === 2 && players[0] && players[1]) {
                const p0 = players[0];
                const p1 = players[1];
                if (
                    (p0.user_id === userId1 && p1.user_id === userId2) ||
                    (p0.user_id === userId2 && p1.user_id === userId1)
                ) {
                    if (p0.score != null && p1.score != null) {
                        if (p0.score > p1.score) return p0.user_id;
                        if (p1.score > p0.score) return p1.user_id;
                    }
                }
            }
        }
        return null; // Aucun match direct ou égalité
    };

    // Trier avec critère de match direct
    return Object.values(stats).sort((a, b) => {
        // 1. Trier par victoires (descendant)
        if (b.wins !== a.wins) return b.wins - a.wins;
        // 2. Trier par manches (descendant)
        if (b.points !== a.points) return b.points - a.points;
        // 3. Trier par match direct
        const directWinnerId = getDirectMatchWinner(a.user_id, b.user_id);
        if (directWinnerId === a.user_id) return -1; // a gagne contre b
        if (directWinnerId === b.user_id) return 1;  // b gagne contre a
        // 4. Si aucun match direct ou égalité, trier par user_id (arbitraire)
        return a.user_id - b.user_id;
    });
}

/**
 * Trouve le gagnant d'un match à 2 joueurs
 */
export function getMatchWinner(match: Match): MatchPlayer | null {
    if (!match.players || match.players.length !== 2) return null;
    const [p1, p2] = match.players;
    if (!p1 || !p2) return null;
    if (p1.score == null || p2.score == null) return null;
    if (p1.score > p2.score) return p1;
    if (p2.score > p1.score) return p2;
    return null; // égalité
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
            players: [
                { user_id: w1.user_id, name: w1.name, score: null },
                { user_id: w2.user_id, name: w2.name, score: null }
            ],
            status: 'pending',
            round: 3,
            pool_id: undefined
        }];
    }
    return [];
}
