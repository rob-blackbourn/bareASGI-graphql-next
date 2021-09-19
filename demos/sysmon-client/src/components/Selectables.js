import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormControl from '@mui/material/FormControl';
import FormLabel from '@mui/material/FormLabel';

export const renderRequestTypeSelector = (requestType, clientType, handler) => (
  <FormControl component="fieldset">
    <FormLabel component="legend">Request Type</FormLabel>
    <RadioGroup
      aria-label="requestType"
      name="request-radio-buttons-group"
      value={requestType}
      onChange={handler}
    >
      <FormControlLabel value="query" control={<Radio />} label="Query" />
      <FormControlLabel
        value="subscription"
        control={<Radio disabled={clientType==='fetch'}/>}
        label="Subscription"
      />
    </RadioGroup>
  </FormControl>
)

export const renderRequestComplexitySelector = (requestComplexity, handler) => (
  <FormControl component="fieldset">
    <FormLabel component="legend">Request Complexity</FormLabel>
    <RadioGroup
      aria-label="requestComplexity"
      name="request-complexity-radio-buttons-group"
      value={requestComplexity}
      onChange={handler}
    >
      <FormControlLabel value="simple" control={<Radio />} label="Simple" />
      <FormControlLabel value="complex" control={<Radio />} label="Complex" />
    </RadioGroup>
  </FormControl>
)

export const renderClientTypeSelector = (clientType, handler) => (
  <FormControl component="fieldset">
    <FormLabel component="legend">Client</FormLabel>
    <RadioGroup
      aria-label="clientType"
      name="client-radio-buttons-group"
      value={clientType}
      onChange={handler}
    >
      <FormControlLabel value="fetch" control={<Radio />} label="Fetch" />
      <FormControlLabel value="stream" control={<Radio />} label="Stream" />
      <FormControlLabel value="eventSource" control={<Radio />} label="Event Source" />
      <FormControlLabel value="webSocket" control={<Radio />} label="WebSocket" />
    </RadioGroup>
  </FormControl>
)
