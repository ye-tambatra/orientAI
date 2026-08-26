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
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6">OrientAI</Typography>
        <Typography variant="body2" color="text.secondary">
          Assistant d'orientation scolaire
        </Typography>
      </Box>

      <Stack spacing={2} sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
        {messages.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ m: 'auto' }}>
            Posez une question sur les filières, les conditions d'admission...
          </Typography>
        )}

        {messages.map((message) => (
          <Stack
            key={message.id}
            spacing={0.5}
            sx={{ alignItems: message.role === 'user' ? 'flex-end' : 'flex-start' }}
          >
            <Stack direction="row" spacing={1}>
              {message.role === 'assistant' && (
                <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                  <SmartToyIcon fontSize="small" />
                </Avatar>
              )}
              <Paper
                variant="outlined"
                sx={{
                  p: 1.5,
                  maxWidth: '75%',
                  bgcolor: message.role === 'user' ? 'primary.main' : 'background.paper',
                  color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                }}
              >
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {message.content}
                </Typography>
              </Paper>
              {message.role === 'user' && (
                <Avatar sx={{ bgcolor: 'grey.500', width: 32, height: 32 }}>
                  <PersonIcon fontSize="small" />
                </Avatar>
              )}
            </Stack>

            {message.steps && message.steps.length > 0 && (
              <Box sx={{ pl: message.role === 'assistant' ? 5 : 0, maxWidth: '75%' }}>
                <StepsAccordion steps={message.steps} />
              </Box>
            )}

            {message.sources && message.sources.length > 0 && (
              <Box sx={{ pl: message.role === 'assistant' ? 5 : 0 }}>
                <SourcesList sources={message.sources} />
              </Box>
            )}
          </Stack>
        ))}

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
