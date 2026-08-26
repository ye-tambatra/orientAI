import { useEffect, useRef, useState } from 'react'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import IconButton from '@mui/material/IconButton'
import Typography from '@mui/material/Typography'
import Avatar from '@mui/material/Avatar'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import SendIcon from '@mui/icons-material/Send'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import PersonIcon from '@mui/icons-material/Person'
import AssignmentIcon from '@mui/icons-material/Assignment'
import { useChatSession } from './useChatSession'
import StepsAccordion from './StepsAccordion'
import SourcesList from './SourcesList'
import ReactMarkdown from 'react-markdown'
import OrientationSurveyModal from './OrientationSurveyModal'

export default function ChatPage() {
  const { messages, isSending, error, sendMessage } = useChatSession()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const [surveyOpen, setSurveyOpen] = useState(false)
  const [surveyPrefilled, setSurveyPrefilled] = useState<Record<string, string>>({})
  const [surveyQuestions, setSurveyQuestions] = useState<any[]>([])
  const [surveyLabels, setSurveyLabels] = useState<Record<string, string>>({})
  const [handledSurveyMessages, setHandledSurveyMessages] = useState<Set<string>>(new Set())
  const [currentSurveyMessageId, setCurrentSurveyMessageId] = useState<string | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isSending])

  const handleOpenSurvey = (messageId: string, args: Record<string, string>, questions: any[], labels: Record<string, string>) => {
    setSurveyPrefilled(args)
    setSurveyQuestions(questions)
    setSurveyLabels(labels)
    setCurrentSurveyMessageId(messageId)
    setSurveyOpen(true)
  }

  const handleSurveyFinish = (results: Record<string, string>) => {
    setSurveyOpen(false)
    if (currentSurveyMessageId) {
      setHandledSurveyMessages(prev => new Set(prev).add(currentSurveyMessageId))
      setCurrentSurveyMessageId(null)
    }

    const listText = Object.entries(results)
      .map(([key, value]) => `- **${surveyLabels[key] || key} :** ${value || 'Non précisé'}`)
      .join('\n');

    const resultsText = `Résultats du questionnaire d'orientation :\n\n${listText}\n\nPeux-tu analyser mon profil avec ces informations ?`;

    sendMessage(resultsText)
  }

  const handleSend = () => {
    if (!input.trim() || isSending) return
    sendMessage(input)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        maxWidth: 720,
        mx: 'auto',
      }}
    >
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center', gap: 2 }}>
        <img src="/ispm_logo.jpeg" alt="ISPM Logo" style={{ height: 48, width: 'auto', borderRadius: 4 }} />
        <Box>
          <Typography variant="h6" color="primary" sx={{ fontWeight: 'bold' }}>OrientAI</Typography>
          <Typography variant="body2" color="text.secondary">
            Assistant d'orientation scolaire de l'ISPM
          </Typography>
        </Box>
      </Box>

      <Stack spacing={2} sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
        {messages.length === 0 && (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              textAlign: 'center',
              gap: 2,
              px: 2,
            }}
          >
            <SmartToyIcon sx={{ fontSize: 64, color: 'primary.main', opacity: 0.5 }} />
            <Typography variant="h6" color="text.primary" sx={{ fontWeight: 500 }}>
              Comment puis-je vous aider ?
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 400 }}>
              Posez vos questions sur les filières, les conditions d'admission, les tarifs ou la vie étudiante à l'ISPM.
            </Typography>
          </Box>
        )}

        {messages.map((message) => {
          const isUser = message.role === 'user'
          return (
            <Box
              key={message.id}
              sx={{
                display: 'block',
                width: '100%',
                mb: 2,
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'row',
                  alignItems: 'flex-start',
                  width: 'fit-content',
                  maxWidth: '85%',
                  ml: isUser ? 'auto' : 0,
                  mr: !isUser ? 'auto' : 0,
                  gap: 1,
                }}
              >
                {!isUser && (
                  <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32, flexShrink: 0 }}>
                    <SmartToyIcon fontSize="small" />
                  </Avatar>
                )}

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, minWidth: 0 }}>
                  <Paper
                    variant="outlined"
                    sx={{
                      p: 1.5,
                      bgcolor: isUser ? 'primary.main' : 'background.paper',
                      color: isUser ? 'primary.contrastText' : 'text.primary',
                      borderRadius: 2,
                      borderTopRightRadius: isUser ? 0 : 2,
                      borderTopLeftRadius: !isUser ? 0 : 2,
                      wordBreak: 'break-word',
                    }}
                  >
                    <Box
                      sx={{
                        whiteSpace: 'normal',
                        '& p': { m: 0, '&:not(:last-child)': { mb: 1 } },
                        '& a': { color: 'inherit', textDecoration: 'underline' },
                      }}
                    >
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </Box>
                  </Paper>

                  {message.steps && message.steps.length > 0 && (
                    <Box sx={{ width: '100%' }}>
                      <StepsAccordion steps={message.steps} />
                    </Box>
                  )}

                  {message.sources && message.sources.length > 0 && (
                    <Box sx={{ width: '100%', mt: 0.5 }}>
                      <SourcesList sources={message.sources} />
                    </Box>
                  )}

                  {message.steps && (() => {
                    const surveyStep = message.steps.find(s => s.tool === 'demarrer_questionnaire_orientation');
                    if (!surveyStep) return null;
                    const isHandled = handledSurveyMessages.has(message.id);

                    let parsedQuestions: any[] = [];
                    let parsedLabels: Record<string, string> = {};
                    try {
                      const data = JSON.parse(surveyStep.result);
                      parsedQuestions = data.questions || [];
                      parsedLabels = data.labels || {};
                    } catch (e) { }

                    return (
                      <Box sx={{ width: '100%', mt: 1 }}>
                        <Button
                          variant="outlined"
                          color="primary"
                          size="small"
                          disabled={isHandled}
                          startIcon={<AssignmentIcon />}
                          onClick={() => handleOpenSurvey(message.id, surveyStep.args as Record<string, string>, parsedQuestions, parsedLabels)}
                          sx={{ textTransform: 'none', borderRadius: 2 }}
                        >
                          {isHandled ? "Questionnaire terminé" : "Commencer le questionnaire"}
                        </Button>
                      </Box>
                    );
                  })()}
                </Box>

                {isUser && (
                  <Avatar sx={{ bgcolor: 'grey.500', width: 32, height: 32, flexShrink: 0 }}>
                    <PersonIcon fontSize="small" />
                  </Avatar>
                )}
              </Box>
            </Box>
          )
        })}

        {isSending && (
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
            <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
              <SmartToyIcon fontSize="small" />
            </Avatar>
            <CircularProgress size={18} />
          </Stack>
        )}

        {error && <Alert severity="error">{error}</Alert>}

        <div ref={bottomRef} />
      </Stack>

      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Stack direction="row" spacing={1}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Écrivez votre message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            size="small"
          />
          <IconButton
            color="primary"
            onClick={handleSend}
            disabled={!input.trim() || isSending}
            aria-label="Envoyer"
          >
            <SendIcon />
          </IconButton>
        </Stack>
      </Box>

      <OrientationSurveyModal
        open={surveyOpen}
        prefilledData={surveyPrefilled}
        questions={surveyQuestions}
        onFinish={handleSurveyFinish}
        onClose={() => setSurveyOpen(false)}
      />
    </Box>
  )
}
