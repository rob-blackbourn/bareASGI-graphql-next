import PropTypes from 'prop-types'
import Radio from '@mui/material/Radio'
import RadioGroup from '@mui/material/RadioGroup'
import FormControlLabel from '@mui/material/FormControlLabel'
import FormControl from '@mui/material/FormControl'
import FormLabel from '@mui/material/FormLabel'

function ClientTypeSelector({ clientType, handler }) {
  return (
    <FormControl component="fieldset">
      <FormLabel component="legend">Client</FormLabel>
      <RadioGroup
        aria-label="clientType"
        name="client-type-radio-buttons-group"
        value={clientType}
        onChange={handler}
      >
        <FormControlLabel value="fetch" control={<Radio />} label="Fetch" />
        <FormControlLabel value="stream" control={<Radio />} label="Stream" />
        <FormControlLabel
          value="eventSource"
          control={<Radio />}
          label="Event Source"
        />
        <FormControlLabel
          value="webSocket"
          control={<Radio />}
          label="WebSocket"
        />
      </RadioGroup>
    </FormControl>
  )
}

ClientTypeSelector.propTypes = {
  clientType: PropTypes.string.isRequired,
  handler: PropTypes.func.isRequired
}

export default ClientTypeSelector
