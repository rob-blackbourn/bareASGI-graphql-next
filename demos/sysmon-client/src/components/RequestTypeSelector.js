import PropTypes from 'prop-types'
import Radio from '@mui/material/Radio'
import RadioGroup from '@mui/material/RadioGroup'
import FormControlLabel from '@mui/material/FormControlLabel'
import FormControl from '@mui/material/FormControl'
import FormLabel from '@mui/material/FormLabel'

function RequestTypeSelector({ requestType, clientType, handler }) {
  return (
    <FormControl component="fieldset">
      <FormLabel component="legend">Request Type</FormLabel>
      <RadioGroup
        aria-label="requestType"
        name="request-type-radio-buttons-group"
        value={requestType}
        onChange={handler}
      >
        <FormControlLabel value="query" control={<Radio />} label="Query" />
        <FormControlLabel
          value="subscription"
          control={<Radio disabled={clientType === 'fetch'} />}
          label="Subscription"
        />
      </RadioGroup>
    </FormControl>
  )
}

RequestTypeSelector.propTypes = {
  requestType: PropTypes.string.isRequired,
  clientType: PropTypes.string.isRequired,
  handler: PropTypes.func.isRequired
}

export default RequestTypeSelector
