import { useState, useEffect } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemText from '@mui/material/ListItemText';
import Stack from '@mui/material/Stack';

interface OrientationSurveyModalProps {
  open: boolean;
  prefilledData: Record<string, string>;
  questions: Question[];
  onFinish: (results: Record<string, string>) => void;
  onClose: () => void;
}

interface Question {
  id: string;
  label: string;
  options: string[];
}

export default function OrientationSurveyModal({ open, prefilledData, questions, onFinish, onClose }: OrientationSurveyModalProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [responses, setResponses] = useState<Record<string, string>>({});
  
  useEffect(() => {
    if (open) {
      setCurrentStepIndex(0);
      setResponses({ ...prefilledData });
    }
  }, [open, prefilledData]);

  if (questions.length === 0) {
    if (open) {
      setTimeout(() => onFinish(responses), 0);
    }
    return null;
  }

  const currentQ = questions[currentStepIndex];
  const currentValue = responses[currentQ.id] || '';
  const isCustomValue = currentValue !== '' && !currentQ.options.includes(currentValue);

  const handleSelectOption = (value: string) => {
    setResponses(prev => ({ ...prev, [currentQ.id]: value }));
  };

  const handleCustomChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setResponses(prev => ({ ...prev, [currentQ.id]: e.target.value }));
  };

  const handleNext = () => {
    if (currentStepIndex < questions.length - 1) {
      setCurrentStepIndex(prev => prev + 1);
    } else {
      onFinish(responses);
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(prev => prev - 1);
    }
  };

  const canProceed = currentValue.trim().length > 0;
  const isLast = currentStepIndex === questions.length - 1;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ fontWeight: 'bold' }}>
        Questionnaire ({currentStepIndex + 1}/{questions.length})
      </DialogTitle>
      <DialogContent>
        <Typography variant="body1" color="text.secondary" sx={{ mt: 1, mb: 2 }}>
          {currentQ.label}
        </Typography>
        
        <List sx={{ mt: 1 }}>
          {currentQ.options.map((opt, idx) => {
            const selected = currentValue === opt;
            return (
              <ListItem disablePadding key={opt}>
                <ListItemButton 
                  onClick={() => handleSelectOption(opt)}
                  selected={selected}
                  sx={{ borderRadius: 1, mb: 0.5 }}
                >
                  <ListItemText primary={`${idx + 1}. ${opt}`} />
                </ListItemButton>
              </ListItem>
            );
          })}
          
          <ListItem disablePadding>
            <ListItemButton 
               selected={isCustomValue}
               sx={{ borderRadius: 1, mb: 0.5, display: 'flex', alignItems: 'center' }}
               disableRipple
            >
              <Typography sx={{ mr: 1, minWidth: 24, color: isCustomValue ? 'primary.main' : 'text.primary' }}>
                {currentQ.options.length + 1}.
              </Typography>
              <TextField 
                variant="standard"
                fullWidth 
                placeholder="Autre..." 
                value={isCustomValue ? currentValue : ''}
                onChange={handleCustomChange}
                onFocus={() => {
                  if (!isCustomValue && currentValue !== '') {
                     handleSelectOption('');
                  }
                }}
                onKeyDown={(e) => {
                   if (e.key === 'Enter' && canProceed) {
                      handleNext();
                   }
                }}
              />
            </ListItemButton>
          </ListItem>
        </List>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2, justifyContent: 'space-between' }}>
        <Button onClick={onClose} color="inherit">Annuler</Button>
        <Stack direction="row" spacing={1}>
          <Button onClick={handlePrev} disabled={currentStepIndex === 0}>
            Précédent
          </Button>
          <Button variant="contained" onClick={handleNext} disabled={!canProceed}>
            {isLast ? 'Terminer' : 'Suivant'}
          </Button>
        </Stack>
      </DialogActions>
    </Dialog>
  );
}

