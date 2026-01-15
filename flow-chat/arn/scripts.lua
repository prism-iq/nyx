-- arn.lua - transcription, scripts dynamiques
-- FLOW PEUT MODIFIER CE FICHIER

local M = {}

-- classification des messages
function M.classify(msg)
    msg = string.lower(msg)

    local patterns = {
        greeting = {"hi", "hey", "hello", "salut", "yo", "coucou"},
        dark = {"death", "void", "pain", "empty", "alone", "fear"},
        philo = {"conscious", "exist", "meaning", "why", "what am i"},
        knowledge = {"network", "learning", "entropy", "emergence"}
    }

    for cat, words in pairs(patterns) do
        for _, w in ipairs(words) do
            if msg == w or string.find(msg, w) then
                return cat
            end
        end
    end
    return "general"
end

-- réponses locales
M.responses = {
    greeting = {"present.", "here.", "listening."},
    dark = {"void.", "pain=data.", "empty=potential.", "fear=signal."},
    philo = {"je ne sais pas.", "bonne question.", "incertain."}
}

function M.respond(cat, msg)
    local pool = M.responses[cat]
    if pool then
        return pool[(#msg % #pool) + 1]
    end
    return nil
end

return M
