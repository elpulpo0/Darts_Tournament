import { useTournamentStore } from '../stores/useTournamentStore';

export const getParticipantDisplayName = (participant: MatchParticipantSchema | Participant | null): string => {
    const tournamentStore = useTournamentStore();
    if (!participant) return 'N/A';

    let fullParticipant: MatchParticipantSchema | Participant = participant;
    // Check for participant_id (MatchParticipantSchema) or id (Participant)
    const participantId = 'participant_id' in participant ? participant.participant_id : participant.id;
    if ((!participant.users || participant.users.length === 0) && participantId) {
        const storedParticipant = tournamentStore.participants.find(p => p.id === participantId);
        if (storedParticipant) {
            fullParticipant = storedParticipant;
        }
    }

    const baseName = fullParticipant.name || (fullParticipant.users?.length === 1 ? fullParticipant.users[0]?.name || 'N/A' : 'N/A');
    if (fullParticipant.users?.length === 2) {
        const userNames = fullParticipant.users.map(u => u.name || 'Unknown').join(' & ');
        return `${baseName} (${userNames})`;
    }

    return baseName;
};