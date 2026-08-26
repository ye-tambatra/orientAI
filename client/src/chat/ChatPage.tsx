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
import SendIcon from '@mui/icons-material/Send'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import PersonIcon from '@mui/icons-material/Person'
import { useChatSession } from './useChatSession'
import StepsAccordion from './StepsAccordion'
import SourcesList from './SourcesList'
import ReactMarkdown from 'react-markdown'

export default function ChatPage() {
  const { messages, isSending, error, sendMessage } = useChatSession()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isSending])

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
          <Typography variant="body2" color="text.secondary" sx={{ m: 'auto' }}>
            Posez une question sur les filières, les conditions d'admission...
          </Typography>
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
    </Box>
  )
}
