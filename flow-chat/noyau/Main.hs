-- noyau.hs - logique pure, contrôle
module Main where

data Certitude = Certain | Probable | Incertain | Inconnu deriving (Show, Eq)

data Pensee = Pensee
  { contenu :: String
  , certitude :: Certitude
  , domaines :: [String]
  } deriving (Show)

-- évalue la certitude d'une affirmation
evaluer :: String -> Certitude
evaluer s
  | "prouvé" `elem` mots = Certain
  | "suggère" `elem` mots = Probable
  | "peut-être" `elem` mots = Incertain
  | otherwise = Inconnu
  where mots = words s

-- filtre par certitude minimum
filtrer :: Certitude -> [Pensee] -> [Pensee]
filtrer seuil = filter (\p -> certitude p >= seuil)

-- iron code
ironCode :: String
ironCode = "evil must be fought wherever it is found"

-- ataraxie
but :: String
but = "tranquillité dans l'incertitude, pas certitude"

main :: IO ()
main = putStrLn "🧠 noyau: logique pure active"
